from optparse import OptionParser
import dnsconfig
import os, sys

def main():
    parser = OptionParser()
    parser.add_option('-c', '--config', dest='config', help='use FILE as the config file', metavar='FILE')
    parser.add_option('-f', '--force', dest='force', help='force reloading all zones and config files', action="store_true")
    parser.add_option('-m', '--master', dest='master', help='create master configuration (default)', action="store_true")
    parser.add_option('-s', '--slave', dest='slave', help='create slave configuration', action="store_true")
    parser.set_defaults(config='/etc/dnsconfig.conf')
    
    (options, args) = parser.parse_args()
    
    if (not os.path.exists(options.config)):
        sys.stderr.write('Config %(file)s not found.\n' % { 'file' : options.config })
        sys.exit(1)
        
    if (options.master and options.slave):
        sys.stderr.write("Can't create master and slave config in the same time.")
        sys.exit(1)
    
    try:
        dns = None
        if (options.slave):
            dns = dnsconfig.SlaveConfig(options.config, options.force)
        else:
            dns = dnsconfig.MasterConfig(options.config, options.force)    
        dns.execute()
    except KeyboardInterrupt:
        sys.stderr.write('Update aborted, config is possibly inconsistent now!\n')
        sys.exit(1)
    except Exception, exp:
        sys.stderr.write("An error occurred: %s\n" % exp)
        sys.exit(1)