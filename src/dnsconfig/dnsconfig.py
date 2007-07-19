import ConfigParser, ldapobject, pickle, os, sys, datetime
from zone import Zone

class DnsConfig:
    __templates = {}
    
    def __init__(self, file):
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
        
    def __load_zones(self):
        zones = self.__ldap_base.get_children('(&(objectClass=dNSZone)(relativeDomainName=#))', True)
        serials = {}
        zoneobjects = []

        for zone in zones:
            z = Zone(zone)
            serials[z.zonename[0]] = self.__get_serial(z.soa)
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
            
    def __get_serial(self, soa):
        return self.__parse_soa(soa)['serial']
    
    def __parse_soa(self, record):
        parts = record[0].split(' ')
        if (len(parts) == 7):
            return {'ns' : parts[0], 
                    'admin' : parts[1], 
                    'serial' : parts[2],
                    'refresh' : parts[3],
                    'retry' : parts[4],
                    'expiry' : parts[5],
                    'ttl' : parts[6]}
        return None  
    
    def __update_zone(self, zone):
        zone.soa = self.__parse_soa(zone.soa)
        execfile(self.__templates['zone'], globals(), locals())
        zonefile = locals()['result']
        return zonefile.expandtabs(4)
    
    def __create_config(self, zones):
        file = self.__config.get('options', 'configfile')
        type = self.__config.get('options', 'type')
        dir = self.__config.get('options', 'zoneprefix')
        execfile(self.__templates['config'], globals(), locals())
        fd = open(file, 'w')
        fd.write(locals()['result'].expandtabs(4))
        fd.close()
    
    def execute(self):
        config = self.__load_zones()
        old_serials = self.__load_serials()
        
        zonedir = self.__config.get('options', 'zonedir')
        
        for zone in config[0]:
            new_serial = self.__get_serial(zone.soa)
            name = zone.zonename[0]
            if (not old_serials.has_key(name) or new_serial != old_serials[name]):
                fd = open(os.path.join(zonedir, name), 'w')
                fd.write(self.__update_zone(zone))
                fd.close()
        self.__create_config(config[0])
        self.__store_serials(config[1])