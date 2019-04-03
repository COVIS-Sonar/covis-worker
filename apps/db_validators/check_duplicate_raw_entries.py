import logging

from covis_db import db,hosts,remote,misc

def run( args, run ):

    raws = run.raw
    print(raws)

    sites = list(set([raw.host for raw in raws]))

    logging.info("    Basename has %d raw entries for %d sites" % (len(raws), len(sites)) )


    if len(raws) > len(sites):
        logging.info("   !!! More raw entries than sites for %s" % run.basename)

        ## What's an elegant way to do this?
        s = {}
        for r in raws:
            if r.host not in s:
                s[r.host] = [r]
            else:
                s[r.host].append(r)

        for host,raws in s.items():

            if len(raws) > 1:
                logging.info("   !!! Multiple entries for host %s" % host)

                for r in raws:
                    if host=="COVIS-NAS" and "filesize" not in r.json:
                        logging.info("   !!! Found a COVIS-NAS entry without a size, dropping...")

                        if args.fix and run.collection:
                            run.collection.find_one_and_update({'basename': run.basename},
                                 {'$pull': {'raw': {'host': 'COVIS-NAS', 'filesize': {'$exists': False }  }}} )

                        continue
