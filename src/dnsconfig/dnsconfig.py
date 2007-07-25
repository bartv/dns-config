import ConfigParser, ldapobject, pickle, os, sys, datetime, shutil, popen2
from zone import LdapZone, RelativeZone

class DnsConfig:
    __templates = {}
    __force = False
    __defaults = {}
    
    def __init__(self, file, force):
        self.__force = force
        config = ConfigParser.SafeConfigParser()
        config.read(file)
        self.__config = config
        
        uri = config.get('ldap', 'uri')
        basedn = config.get('ldap', 'basedn')
        self.__ldap_base = ldapobject.init(uri, basedn)            
        
        self.__template_dir = config.get('templates', 'dir')
        for name, value in config.items('templates'):
            if (name != 'dir'):
                self.__templates[name] = os.path.join(self.__template_dir, value)
                
        for name, value in config.items('defaults'):
            self.__defaults[name] = value
        
    def __load_zones(self):
        zones = self.__ldap_base.get_children('(&(objectClass=dNSZone)(sOARecord=*))', True)
        serials = {}
        zoneobjects = []

        for zone in zones:
            z = LdapZone(zone.zoneName[0], zone)
            soa = z.get_soa()
            serials[z.get_zonename()] = soa['serial']
            zoneobjects.append(z)
            
        return (zoneobjects, serials)
            
    def __store_serials(self, serials):
        path = os.path.join(self.__config.get('options', 'statedir'), 'serials.cache')
        fd = open(path, 'w')
        pickle.dump(serials, fd)
        fd.close()
    
    def __load_serials(self):
        path = os.path.join(self.__config.get('options', 'statedir'), 'serials.cache')
        if (not os.path.exists(path)):
            return {}
        fd = open(path, 'r')
        try:
            serials = pickle.load(fd)
        except:
            return {}
        fd.close()
        return serials
            
    def __create_config(self, zones, type):
        # load settings
        configfile = self.__config.get('options', 'configfile')
        dir = self.__config.get('options', 'zoneprefix')
        masters = self.__config.get('options', 'masters').split(',')
        transfer_source = self.__config.get('options', 'transfer-source')
        
        # run template
        execfile(self.__templates['config'], globals(), locals())
        
        # replace config if valid
        backupfile = None
        if (os.path.exists(configfile)):
            backupfile = os.path.join(self.__config.get('options', 'statedir'), 'config-%s' % datetime.datetime.now().strftime("%Y%m%d%H%M"))
            shutil.copyfile(configfile, backupfile)
        
        fd = open(configfile, 'w')
        fd.write(locals()['result'].expandtabs(4))
        fd.close()
        return
        if (not self.__check_config(configfile)):
            # revert config
            shutil.copyfile(backupfile, configfile)
            sys.stderr.write("Config error, reverting config.\n")
            
    def __update_defaults(self, zone):
        rrlist = zone.get_relative_zones()
        main = rrlist['@']
        
        # check if nameservers are defined
        if (not main.has_rr('ns')):
            main.set_rr('ns', [self.__defaults['ns'], self.__defaults['ns2']])
        
        # check if an a record is defined
        if (not main.has_rr('a')):
            main.set_rr('a', [self.__defaults['host']])
            
        # check for mx records
        if (not main.has_rr('mx')):
            if (self.__defaults.has_key('ttlmx')):
                main.set_ttl('mx', self.__defaults['ttlmx'])
                
            mx = []
            for i in range(1,100):
                key = 'mx%d' % i
                if (self.__defaults.has_key(key)):
                    mx.append(self.__defaults[key])
                else:
                    break
            main.set_rr('mx', mx)
            
        # add localhost entry
        if (self.__defaults['localhost'] == 'true' and not rrlist.has_key('localhost')):
            localhost = RelativeZone(zone, 'localhost')
            localhost.set_rr('a', ['127.0.0.1'])
        
        # add a ns alias
        if (self.__defaults['nsalias'] == 'true' and not rrlist.has_key('ns')):
            ns = RelativeZone(zone, 'ns')
            ns.set_rr('a', [self.__defaults['ns']])
            
        # check if there is a www entry
        if (self.__defaults.has_key('webhost') and not (rrlist.has_key('www') or rrlist.has_key('*'))):
            www = RelativeZone(zone, 'www')
            www.set_rr('a', [self.__defaults['webhost']])
            
    def __prepare_rr(self, record):
        list = []
        relativename = record.get_name()
        items = record.get_rr_list()
        for type in items:
            rr = record.get(type)
            list.append((relativename, rr[1], type, rr[0]))
        return list
            
    def __update_zone(self, zone, now):
        name = zone.get_zonename()
        defaults = self.__defaults
        zonedir = self.__config.get('options', 'zonedir')
        
        print "Updating %s with serial %s" % (name, zone.get_soa()['serial'])
        
        zone.load_relative_zones()
        self.__update_defaults(zone)
        
        data = {}
        rrlist = zone.get_relative_zones()
        for i, rr in rrlist.items():
            data[i] = self.__prepare_rr(rr)
        
        execfile(self.__templates['zone'], globals(), locals())
        newzoneconfig = locals()['result'].expandtabs(4)
        
        zonefile = os.path.join(zonedir, name)
        backupfile = None
        
        # backup zone
        if (os.path.exists(zonefile)):
            backupfile = os.path.join(self.__config.get('options', 'statedir'), '%s-%s' % (name, now))
            shutil.copyfile(zonefile, backupfile)
        
        # update zone
        fd = open(os.path.join(zonedir, name), 'w')
        fd.write(newzoneconfig)
        fd.close()
        
        if (not self.__check_zone(name, zonefile)):
            sys.stderr.write("Zonecheck of zone %s failed, reverting changes.\n" % name)
            # revert config
            if (backupfile == None):
                os.remove(zonefile)
                # there isn't a previous version, so remove the zone from the config
                raise Exception("No previous zone file")
            else:
                #shutil.copyfile(backupfile, zonefile)
                return False
        else:
            return True
                    
    def execute(self):
        if (self.__force):
            print "Forcing reload of zone files."
        
        config = self.__load_zones()
        old_serials = self.__load_serials()
        
        updated = []   # list of updated zones
        zones = []     # list of valid zones to include
        now = datetime.datetime.now().strftime("%Y%m%d%H%M")
        type = self.__config.get('options', 'type')
        
        for zone in config[0]:
            #try:
                name = zone.get_zonename()
                if (type == 'master'):
                    new_serial = zone.get_soa()['serial']
                    if (self.__force or not old_serials.has_key(name) or new_serial != old_serials[name]):
                        if (self.__update_zone(zone, now)):
                            updated.append(zone)
                zones.append(name)
            #except Exception, e:
            #    pass
        
        self.__create_config(zones, type)
        self.__store_serials(config[1])
        
        # reload the config
        if (len(updated) > 0 or type != 'master'):
            reloadcmd = self.__config.get('server', 'reload')
            o = popen2.Popen4(reloadcmd)
            exit = o.wait()
            if (exit > 0):
                sys.stderr.write("Error reloading dns server configuration.\n")
    
    def __check_zone(self, zonename, zonefile):
        cmd = self.__config.get('server', 'zonecheck')
        cmd = cmd.replace('$(zone)', zonename)
        cmd = cmd.replace('$(file)', zonefile)
        o = popen2.Popen4(cmd)
        exit = o.wait()
        if (exit > 0):
            print o.fromchild.read()
            return False
        return True
    
    def __check_config(self, configfile):
        cmd = self.__config.get('server', 'configcheck')
        cmd = cmd.replace('$(file)', configfile)
        o = popen2.Popen4(cmd)
        exit = o.wait()
        if (exit > 0):
            return False
        return True
