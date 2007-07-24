result  = '; Auto generated zone file from ldap at %s\n' % datetime.datetime.now().strftime("%d/%m/%Y -- %H:%M")
result += '; dn: %s\n\n' % zone.get_dn()

ttl = zone.get_ttl()
if (ttl > 0):
    result += '$TTL %s\n' % ttl
else:
    result += '$TTL %s\n' % defaults['ttl']

soa = zone.get_soa()
result += "@           IN  SOA %s %s (\n" % (soa['ns'], soa['admin']) 
result += "                    %s    ; serial\n" % soa['serial']
result += "                    %s        ; refresh\n" % soa['refresh']
result += "                    %s        ; retry\n" % soa['retry']
result += "                    %s        ; expiry\n" % soa['expiry']
result += "                    %s        ; ttl\n" % soa['ttl']
result += "                )\n\n"

zone.load_relative_zones()
rr = zone.get_relative_zones()
main = rr['@']

# create a list of spaces
spaces = ' '.join([''] * 40)

# how much spaces should be added to align everything
def sp(rel):
    rellen = len(rel)
    size = (rellen/4) + 4
    if (size < 12):
        return 12
    return size

def create_relative(record):
    global spaces, sp
    relative = record.get_name()
    padding = sp(relative)
    padding = 12
    items = record.get_rr_list()
    data = relative.ljust(padding)
    add = ''
    result = ''
    for item in items:
        if (item == 'soa'):
            continue
        resource_record = record.get(item)
        if (resource_record[1] > 0):
            part = '%s\tIN\t%s ' % (resource_record[1], item.upper())
        else:
            part = 'IN\t%s ' % item
        for s in resource_record[0]:
            data += add + part + s + '\n'
            add = spaces[:padding]
    if (len(add) > 0):
        result += data + '\n'
    return result

## adding defaults if needed
result += create_relative(main)

# check if nameservers are defined
if (not main.has_rr('ns')):
    str = '%sIN NS %s\n'
    result += str % (spaces[:12], defaults['ns']) 
    result += str % (spaces[:12], defaults['ns2'])
    result += '\n'

# check if an a record is defined
if (not main.has_rr('a')):
    result += spaces[:12] + 'IN A %s\n\n' % defaults['host']
    
# check for mx records
if (not main.has_rr('mx')):
    str = '%sIN MX %s\n'
    for k, v in defaults.items():
        if (k[:2] == 'mx'):
            result += str % (spaces[:12], v)
    result += '\n'


# add all defined resource records
for name, record in rr.items():
    if (name != '@'):
        result += create_relative(record)
