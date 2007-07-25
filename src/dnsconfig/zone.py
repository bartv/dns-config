class LdapZone:
    __ldap_entry = None
    __zone_name = None
    __relative_part = {}
    __ttl = -1
    __soa = None
        
    def __init__(self, name, entry):
        self.__zone_name = name
        self.__ldap_entry = entry
        self.__append = []
        
        if (hasattr(entry, 'dNSTTL')):
            self.__ttl = entry.dNSTTL[0]
        else:
            self.__ttl = -1
            
        if (hasattr(entry, 'sOARecord')):
            self.__soa = entry.sOARecord[0]
            self.__soa = self.__parse_soa(self.__soa)
        else:
            self.__soa = None
        
        self.__relative_part = {}
        
    def append_children(self, zone):
        self.__append.append(zone)
            
    def get_dn(self):
        return self.__ldap_entry.dn
        
    def load_relative_zones(self):
        entry = self.__ldap_entry
        # load main @ first
        relative = RelativeZone(self, '@')
        self.__add_attributes(relative, entry)
        self.__relative_part['@'] = relative
        
        # now the children
        self.__load_children(entry, self.get_zonename())
        
        # load children of appended domains
        for zone in self.__append:
            self.__load_children(zone, zone.zoneName[0])
    
    def __load_children(self, entry, name):
        children = entry.get_children('(&(objectClass=dNSzone)(zoneName=%s))' % name, False)
        for child in children:
            name = child.relativeDomainName[0]
            relative = None
            if (not self.__relative_part.has_key(name)):
                relative = RelativeZone(self, name)
                self.__relative_part[name] = relative
            else:
                relative = self.__relative_part[name]
            self.__add_attributes(relative, child)
        
    def __add_attributes(self, relative, entry):
        ttl = -1
        if (hasattr(entry, 'dNSTTL')):
            ttl = entry.dNSTTL[0]
        for attribute in dir(entry):
            name = relative.convert_name(attribute)
            if (name != None):
                relative.set_rr(name, getattr(entry, attribute))
                if (ttl > 0):
                    relative.set_ttl(name, ttl)
    
    def get_relative_zones(self):
        return self.__relative_part
    
    def get_zonename(self):
        return self.__zone_name
    
    def get_ttl(self):
        return self.__ttl
    
    def get_soa(self):
        return self.__soa
    
    def __parse_soa(self, record):
        parts = record.split(' ')
        if (len(parts) == 7):
            return {
                    'ns'        : parts[0], 
                    'admin'     : parts[1], 
                    'serial'    : parts[2],
                    'refresh'   : parts[3],
                    'retry'     : parts[4],
                    'expiry'    : parts[5],
                    'ttl'       : parts[6],
                   }
        return None 
    
class RelativeZone:
    __relative_name = None
    __rr = {}
    __ttl = {}
    __zone = None
    __ldap_attributes = {
        'sOARecord' : 'soa',
        'aRecord' : 'a', 
        'mDRecord' : 'md', 
        'mXRecord' : 'mx', 
        'nSRecord' : 'ns', 
        'cNAMERecord' : 'cname', 
        'pTRRecord' : 'ptr', 
        'hINFORecord' : 'hinfo', 
        'mINFORecord' : 'minfo', 
        'tXTRecord' : 'txt', 
        'aFSDBRecord' : 'afsdb', 
        'sIGRecord' : 'sig', 
        'kEYRecord' : 'key', 
        'aAAARecord' : 'aaaa', 
        'lOCRecord' : 'loc', 
        'nXTRecord' : 'nxt', 
        'sRVRecord' : 'srv', 
        'nAPTRRecord' : 'naptr', 
        'kXRecord' : 'kx', 
        'cERTRecord' : 'cert', 
        'a6Record' : 'a6', 
        'dNAMERecord' : 'dname', 
        'dSRecord' : 'ds', 
        'sSHFPRecord' : 'sshfpr', 
        'rRSIGRecord' : 'rrsig', 
        'nSECRecord' : 'nsec', 
    }
    
    def __init__(self, zone, name):
        self.__zone = zone
        self.__relative_name = name
        self.__ttl = {}
        self.__rr = {}
        
    def get_rr_list(self):
        return self.__rr.keys()

    def set_ttl(self, name, ttl):
        self.__ttl[name] = ttl
    
    def get_ttl(self, name):
        if (self.__ttl.has_key(name)):
            return self.__ttl[name]
        return -1
    
    def set_rr(self, name, value):
        self.__rr[name] = value
        
    def get_rr(self, name):
        if (self.__rr.has_key(name)):
            return self.__rr[name]
        return None
    
    def has_rr(self, name):
        return self.__rr.has_key(name)
    
    def get_name(self):
        return self.__relative_name
    
    def get(self, name):
        value = self.get_rr(name)
        ttl = self.get_ttl(name)
        if (value != None):
            return (value, ttl)
        return None
    
    def convert_name(self, name):
        if (self.__ldap_attributes.has_key(name)):
            return self.__ldap_attributes[name]
        return None
