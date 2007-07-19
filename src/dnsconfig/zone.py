class Zone:
    # ldap attributes
    _ldap_attributes = [
        ('zoneName', 'zonename'),
        ('sOARecord', 'soa'),
        ('dNSTTL', 'dnsttl'),
        ('relativeDomainName', 'relativename'),
        ('dNSClass', 'dnsclass'), 
        ('aRecord', 'a'), 
        ('mDRecord', 'md'), 
        ('mXRecord', 'mx'), 
        ('nSRecord', 'ns'), 
        ('cNAMERecord', 'cname'), 
        ('pTRRecord', 'ptr'), 
        ('hINFORecord', 'hinfo'), 
        ('mINFORecord', 'minfo'), 
        ('tXTRecord', 'txt'), 
        ('aFSDBRecord', 'afsdb'), 
        ('sIGRecord', 'sig'), 
        ('kEYRecord', 'key'), 
        ('aAAARecord', 'aaaa'), 
        ('lOCRecord', 'loc'), 
        ('nXTRecord', 'nxt'), 
        ('sRVRecord', 'srv'), 
        ('nAPTRRecord', 'naptr'), 
        ('kXRecord', 'kx'), 
        ('cERTRecord', 'cert'), 
        ('a6Record', 'a6'), 
        ('dNAMERecord', 'dname'), 
        ('dSRecord', 'ds'), 
        ('sSHFPRecord', 'sshfpr'), 
        ('rRSIGRecord', 'rrsig'), 
        ('nSECRecord', 'nsec'), 
    ]
    
    def __init__(self, entry):
        for ldap_attribute, attribute in self._ldap_attributes:
            try:
                value = getattr(entry, ldap_attribute)
                setattr(self, attribute, value)
            except AttributeError:
                pass
        rel_zones = entry.get_children()
        self.children = [ Zone(rel) for rel in rel_zones ]
        self.dn = entry.dn
    
    def _diff(self, other):
        new = {}
        modified = {}
        removed = {}
        other_attributes = other.__dict__.copy()
        attributes = self.__dict__.copy()
        for attr in self.__dict__.keys():
            if (attr[:1] == '_'):
                del other_attributes[attr]
                continue
            # check for new values and modified ones
            try:
                other_val = other_attributes[attr]
                val = attributes[attr]
                if (not other_val == val):
                    modified[attr] = (other_val, val)
                del other_attributes[attr]
            except KeyError:
                new[attr] = attributes[attr]
        # list in other_attributes are the ones that were removed
        for attr in other_attributes.keys():
            if (not modified.has_key(attr)):
                removed[attr] = other_attributes[attr]
            
        return (new, modified, removed)

    def __getstate__(self):
        dict = self.__dict__.copy()
        for a in dict.keys():
            if (a[:1] == '_'):
                del dict[a]
        return dict
    
    def __setstate__(self, dict):
        for a in dict:
            setattr(self, a, dict[a])