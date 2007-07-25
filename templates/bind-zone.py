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
    if (size < 16):
        return 16
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
            part = '%s\tIN %s ' % (resource_record[1], item.upper())
        else:
            part = 'IN %s ' % item.upper()
        for s in resource_record[0]:
            data += add + part + s + '\n'
            add = spaces[:padding]
    if (len(add) > 0):
        result += data + '\n'
    return result

## adding defaults if needed
# TODO @
main= create_relative(main)

# check if nameservers are defined
if (not main.has_rr('ns')):
    str = '%sIN NS %s\n'
    result += str % (spaces[:16], defaults['ns']) 
    result += str % (spaces[:16], defaults['ns2'])
    result += '\n'

# check if an a record is defined
if (not main.has_rr('a')):
    result += spaces[:16] + 'IN A %s\n\n' % defaults['host']
    
# check for mx records
if (not main.has_rr('mx')):
    if (defaults.has_key('ttlmx')):
        str = '%s' + defaults['ttlmx'] + ' IN MX %s\n'
    else:
        str = '%sIN MX %s\n'
    for i in range(1,100):
        key = 'mx%d' % i
        if (defaults.has_key(key)):
            result += str % (spaces[:16], defaults[key])
        else:
            break
    result += '\n'
    
# add localhost entry
if (defaults['localhost'] == 'true' and not rr.has_key('localhost')):
    result += 'localhost' + spaces[:7] + 'IN A\t\t127.0.0.1\n'

# add a ns alias
if (defaults['nsalias'] == 'true' and not rr.has_key('ns')):
    result += 'ns' + spaces[:14] + 'IN CNAME\t%s\n' % defaults['ns']
    
# check if there is a www entry
if (defaults.has_key('webhost') and not (rr.has_key('www') or rr.has_key('*'))):
    result += 'www' + spaces[:13] + 'IN CNAME\t%s\n' % defaults['webhost']
    
result += '\n'

# add all defined resource records
for name, record in rr.items():
    if (name != '@'):
        result += create_relative(record)
