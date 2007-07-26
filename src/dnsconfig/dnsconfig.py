import ConfigParser, ldapobject, pickle, os, sys, datetime, shutil, popen2
from zone import LdapZone, RelativeZone

        
class DnsConfig:
    def __init__(self, file, force):
        self.templates = {}
        self.defaults = {}
        self.force_reload = force
        config = ConfigParser.SafeConfigParser()
        config.read(file)
        self.config = config
        
        uri = config.get('ldap', 'uri')
        basedn = config.get('ldap', 'basedn')
        self.__ldap_base = ldapobject.init(uri, basedn)            
        
        self.__template_dir = config.get('templates', 'dir')
        for name, value in config.items('templates'):
            if (name != 'dir'):
                self.templates[name] = os.path.join(self.__template_dir, value)
                
        for name, value in config.items('defaults'):
            self.defaults[name] = value
            
    def __load_zones(self):
        ''' 
            Load all main records of each zone from ldap, this method also 
            checks if any append directives are included in a zone
        '''
        zones = self.__ldap_base.get_children('(&(objectClass=dNSZone)(sOARecord=*))', True)
        serials = {}
        zoneobjects = []
        zonedict = {}

        append = []
        for zone in zones:
            z = LdapZone(zone.zoneName[0], zone)
            zonedict[zone.zoneName[0]] = zone
            soa = z.get_soa()
            serials[z.get_zonename()] = soa['serial']
            zoneobjects.append(z)
            
            if (hasattr(zone, 'tXTRecord')):
                txt = zone.tXTRecord
                for t in txt:
                    if (t[:7] == 'append:'):
                        append.append((z, t[8:]))
                    zo = 'zone-only: yes'
                    if (t[:len(zo)] == zo):
                        z.set_zoneonly()
                        
        for zone, link in append:
            if (zonedict.has_key(link)):
                linked = zonedict[link]
                zone.append_children(linked)
            
        return (zoneobjects, serials)
            
    def __store_serials(self, serials):
        path = os.path.join(self.config.get('options', 'statedir'), 'serials.cache')
        fd = open(path, 'w')
        pickle.dump(serials, fd)
        fd.close()
    
    def __load_serials(self):
        path = os.path.join(self.config.get('options', 'statedir'), 'serials.cache')
        if (not os.path.exists(path)):
            return {}
        fd = open(path, 'r')
        try:
            serials = pickle.load(fd)
        except:
            return {}
        fd.close()
        return serials
            
    def create_config(self, zones, type):
        ''' 
            Create the configuration of the dns server by executing the defined
            template
        '''
        # load settings
        configfile = self.config.get('options', 'configfile')
        dir = self.config.get('options', 'zoneprefix')
        masters = self.config.get('options', 'masters').split(',')
        type = self.get_type()
        transfer_source = self.config.get('options', 'transfer-source')
        
        # run template
        execfile(self.templates['config'], globals(), locals())
        
        # replace config if valid
        backupfile = None
        if (os.path.exists(configfile)):
            backupfile = os.path.join(self.config.get('options', 'statedir'), 'config-%s' % datetime.datetime.now().strftime("%Y%m%d%H%M"))
            shutil.copyfile(configfile, backupfile)
        
        fd = open(configfile, 'w')
        fd.write(locals()['result'].expandtabs(4))
        fd.close()
        
        if (not self.__check_config(configfile)):
            # revert config
            shutil.copyfile(backupfile, configfile)
            sys.stderr.write("Config error, reverting config.\n")    
            
    def update_defaults(self, zone):
        '''
            Apply default settings if needed
        '''
        rrlist = zone.get_relative_zones()
        main = rrlist['@']
        
        # check if nameservers are defined
        if (not main.has_rr('ns')):
            main.set_rr('ns', [self.defaults['ns'], self.defaults['ns2']])
        
        # check if an a record is defined
        if (not main.has_rr('a')):
            main.set_rr('a', [self.defaults['host']])
            
        # check for mx records
        if (not main.has_rr('mx')):
            if (self.defaults.has_key('ttlmx')):
                main.set_ttl('mx', self.defaults['ttlmx'])
                
            mx = []
            for i in range(1,100):
                key = 'mx%d' % i
                if (self.defaults.has_key(key)):
                    mx.append(self.defaults[key])
                else:
                    break
            main.set_rr('mx', mx)
            
        # add localhost entry
        if (self.defaults['localhost'] == 'true' and not rrlist.has_key('localhost')):
            localhost = RelativeZone(zone, 'localhost')
            localhost.set_rr('a', ['127.0.0.1'])
        
        # add a ns alias
        if (self.defaults['nsalias'] == 'true' and not rrlist.has_key('ns')):
            ns = RelativeZone(zone, 'ns')
            ns.set_rr('a', [self.defaults['ns']])
            
        # check if there is a www entry
        if (self.defaults.has_key('webhost') and not (rrlist.has_key('www') or rrlist.has_key('*'))):
            www = RelativeZone(zone, 'www')
            www.set_rr('a', [self.defaults['webhost']])

    
    def update_zone(self, zone, oldserial, now): 
        '''
            Update the given zone by loading all information needed, executing
            the template and afterwards checking for a valid syntax
        '''
        return False
                    
    def execute(self):
        if (self.force_reload):
            print "Forcing reload."
        
        config = self.__load_zones()
        old_serials = self.__load_serials()
        
        updated = False     # are there any updated zones
        new = False         # is there a new zone
        zones = []          # list of valid zones to include
        now = datetime.datetime.now().strftime("%Y%m%d%H%M")
        
        for zone in config[0]:
            try:
                name = zone.get_zonename()
                if (old_serials.has_key(name)):
                    oldserial = old_serials[name]
                    del old_serials[name]
                else:
                    new = True
                    oldserial = 0
                    
                result = self.update_zone(zone, oldserial, now)
                if (result):
                    updated = True

                zones.append(zone)
            except FileNotFoundException, e:
                ''' 
                    An error occured updating this zone and there wasn't an old
                    zone file to revert back to. If this is the only update we
                    will reload the dns server config for nothing.
                '''
                pass
        
        removed = False
        for zone, serial in old_serials.items():
            removed = True
            self.remove_zone(zone)

        if (new or removed or self.force_reload):
            # there are new zones, create a new config file        
            self.create_config(zones, type)
        
        # reload the config
        self.do_reload(updated, new, removed)
        
        # store serials of all zones
        self.__store_serials(config[1])
        
    def remove_zone(self, zonename):
        print "%s has been removed" % zonename
        
    def do_reload(self, updated, new, removed):
        '''
            Decide if a reload of the server is needed given if there are 
            updated zones and there are new zones. This method should be overriden
            by subclasses. Now a reload is always issued
        '''
        self.__reload_server()
                
    def reload_server(self):
        ''' 
            Execute the dns server reload command 
        ''' 
        reloadcmd = self.config.get('server', 'reload')
        o = popen2.Popen4(reloadcmd)
        exit = o.wait()
        if (exit > 0):
            sys.stderr.write("Error reloading dns server configuration.\n")
    
    def check_zone(self, zonename, zonefile):
        ''' 
            Run the command to check if the zone file is valid 
        '''
        cmd = self.config.get('server', 'zonecheck')
        cmd = cmd.replace('$(zone)', zonename)
        cmd = cmd.replace('$(file)', zonefile)
        o = popen2.Popen4(cmd)
        exit = o.wait()
        if (exit > 0):
            #print o.fromchild.read()
            return False
        return True
    
    def __check_config(self, configfile):
        ''' 
            Check the configuration file of the dns server 
        '''
        cmd = self.config.get('server', 'configcheck')
        cmd = cmd.replace('$(file)', configfile)
        o = popen2.Popen4(cmd)
        exit = o.wait()
        if (exit > 0):
            #print o.fromchild.read()
            return False
        return True
    
    def get_type(self):
        raise NotImplementedError
    
class MasterConfig(DnsConfig):
    def __init__(self, file, force):
        DnsConfig.__init__(self, file, force)
        
    def __prepare_rr(self, record):
        ''' 
            Create a list of tuples with all information for each resource record 
        '''
        list = []
        relativename = record.get_name()
        items = record.get_rr_list()
        for type in items:
            rr = record.get(type)
            list.append((relativename, rr[1], type, rr[0]))
        return list
    
    def update_zone(self, zone, oldserial, now):
        '''
            Update the given zone by loading all information needed, executing
            the template and afterwards checking for a valid syntax
        '''
        serial = zone.get_soa()['serial']
        if (serial == oldserial and not self.force_reload):
            return False # no update needed
        
        name = zone.get_zonename()
        defaults = self.defaults
        zonedir = self.config.get('options', 'zonedir')
        
        print "Updating %s with serial %s" % (name, serial)
        
        zone.load_relative_zones()
        self.update_defaults(zone)
        
        data = {}
        rrlist = zone.get_relative_zones()
        for i, rr in rrlist.items():
            data[i] = self.__prepare_rr(rr)
        
        execfile(self.templates['zone'], globals(), locals())
        newzoneconfig = locals()['result'].expandtabs(4)
        
        zonefile = os.path.join(zonedir, name)
        backupfile = None
        
        # backup zone
        if (os.path.exists(zonefile)):
            backupfile = os.path.join(self.config.get('options', 'statedir'), '%s-%s' % (name, now))
            shutil.copyfile(zonefile, backupfile)
        
        # update zone
        fd = open(os.path.join(zonedir, name), 'w')
        fd.write(newzoneconfig)
        fd.close()
        
        if (not self.check_zone(name, zonefile)):
            sys.stderr.write("Zonecheck of zone %s failed, reverting changes.\n" % name)
            # revert config
            if (backupfile == None):
                os.remove(zonefile)
                # there isn't a previous version, so remove the zone from the config
                raise FileNotFoundException("No previous zone file")
            else:
                #shutil.copyfile(backupfile, zonefile)
                return False
        else:
            return True
        
    def remove_zone(self, zonename):
        DnsConfig.remove_zone(self, zonename)
        # todo: remove zone file
        zonedir = self.config.get('options', 'zonedir')
        zonefile = os.path.join(zonedir, zonename)
        if (os.path.isfile(zonefile)):
            os.remove(zonefile)
            
    def do_reload(self, updated, new, removed):
        # update the config when zones are updated and when they are added
        if (updated or new or self.force_reload or removed):
            self.reload_server()
            
    def get_type(self):
        return 'master'
    

class SlaveConfig(DnsConfig):
    def __init__(self, file, force):
        DnsConfig.__init__(self, file, force)
        
    def do_reload(self, updated, new, removed):
        # only reload the config when zones are added
        if (new or self.force_reload or removed):
            self.reload_server()
            
    def update_config(self, zone, oldserial, now):
        if (oldserial == 0): # it's new
            print "Added zone %s\n" % zone.get_zonename()
            
    def get_type(self):
        return 'slave'

class FileNotFoundException(Exception):
    pass