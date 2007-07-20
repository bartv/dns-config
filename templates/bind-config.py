result  = "// Auto generated from ldap at %s\n\n" % datetime.datetime.now().strftime("%d/%m/%Y -- %H:%M")

for zone in zones:
    result += 'zone "%s" IN {\n' % zone
    result += '\ttype %s;\n' % type
    result += '\tfile "%s/%s";\n' % (dir, zone)
    result += '};\n\n'