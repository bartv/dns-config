result  = "// Auto generated from ldap at %s\n" % datetime.datetime.now().strftime("%d/%m/%Y -- %H:%M")
result += "// vim: ft=named\n\n"

for zone in zones:
    result += 'zone "%s" IN {\n' % zone
    result += '\ttype %s;\n' % type
    result += '\tfile "%s/%s";\n' % (dir, zone)
    if (type == 'slave'):
        result += '\tmasters {\n\t\t';
        result += '\n\t\t'.join(masters) + ';'
        result += '\n\t};\n'
        result += '\ttransfer-source %s\n' % transfer_source
    result += '};\n\n'