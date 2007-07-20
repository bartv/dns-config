attributes = {
    'a'      : 'A', 
    'md'     : 'MD', 
    'mx'     : 'MX', 
    'ns'     : 'NS', 
    'cname'  : 'CNAME', 
    'ptr'    : 'PTR', 
    'hinfo'  : 'HINFO', 
    'minfo'  : 'MINFO', 
    'txt'    : 'TXT', 
    'afsdb'  : 'AFSDB', 
    'sig'    : 'SIG', 
    'key'    : 'KEY', 
    'aaaa'   : 'AAAA', 
    'loc'    : 'LOC', 
    'nxt'    : 'NXT',
    'srv'    : 'SRV',
    'naptr'  : 'NAPTR', 
    'kx'     : 'KX', 
    'cert'   : 'CERT', 
    'a6'     : 'A6', 
    'dname'  : 'DNAME', 
    'ds'     : 'DS', 
    'sshfpr' : 'SSHFP', 
    'rrsig'  : 'RRSIG', 
    'nsec'   : 'NSEC' 
}

result  = '; Auto generated zone file from ldap at %s\n' % datetime.datetime.now().strftime("%d/%m/%Y -- %H:%M")
result += '; dn: %s\n' % zone.dn
result += '; vim: ft=named\n\n'

if (hasattr(zone, 'dnsttl')):
    result += '$TTL %s\n' % zone.dnsttl[0]

result += "@           IN  SOA %s %s (\n" % (zone.soa['ns'], zone.soa['admin']) 
result += "                    %s    ; serial\n" % zone.soa['serial']
result += "                    %s        ; refresh\n" % zone.soa['refresh']
result += "                    %s        ; retry\n" % zone.soa['retry']
result += "                    %s        ; expiry\n" % zone.soa['expiry']
result += "                    %s        ; ttl\n" % zone.soa['ttl']
result += "                )\n\n"

rr = zone.children

spaces = ' '.join([''] * 40)

def sp(rel):
    rellen = len(rel)
    size = (rellen/4) + 4
    if (size < 12):
        return 12
    return size
    
for record in rr:
    relative = record.relativename[0]
    padding = sp(relative)
    items = dir(record)
    data = relative.ljust(padding)
    add = ''
    if (hasattr(record, 'dnsttl')):
        dnsttl = record.dnsttl[0]
    else:
        dnsttl = None
    for item in items:
        if (attributes.has_key(item)):
            if (dnsttl != None):
                part = '%s\tIN\t%s ' % (dnsttl, attributes[item])
            else:
                part = 'IN\t%s ' % attributes[item]
            for s in getattr(record, item):
                data += add + part + s + '\n'
                add = spaces[:padding]
    if (len(add) > 0):
        result += data + '\n'
