# Licensed under the MIT license
# Copyright 2007, Bart Vanbrabant <bart@ulyssis.org> 

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

# find the longest relative part and sort the list
size = 0
main = None
list = []
for name, item in data.items():
    length = len(name)
    if (length > size):
        size = length
    if (name == '@'):
        main = (name, item)
    else:
        list.append((name, item))

size = size + 4
if (size < 12):
    size = 12
    
# create list
items = [main]
items.extend(list)

# create rr of the zone file
for name, item in items:
    if (name == '@'):
        name = ''.ljust(size)
    else:
        name = name.ljust(size)
    for rr in item:
        if (rr[2] == 'soa'):
            continue
        if (rr[1] > 0):
            ttl = rr[1].ljust(8)
        else:
            ttl = ''.ljust(8)
        str = '%s%s IN %s%s\n' % (name, ttl, rr[2].upper().ljust(10), '%s')
        for i in rr[3]:
            result += str % i
            name = ''.ljust(size)
