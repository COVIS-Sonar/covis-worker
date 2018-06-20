import re

re_old_covis_nas = re.compile( r"old-covis-nas(\d+)", re.IGNORECASE)
re_covis_nas     = re.compile( r"covis-nas\Z", re.IGNORECASE)
re_dmas          = re.compile( r"dmas", re.IGNORECASE)

def validate_host(host):
    if is_old_nas(host) or \
        is_nas(host) or \
        is_dmas(host):
        return True

    return False


def is_old_nas(host):
    return re_old_covis_nas.match(host) != None

def is_nas(host):
    return re_covis_nas.match(host) != None

def is_dmas(host):
    return re_dmas.match(host) != None


def best_raw(raws, priority=[re_covis_nas,re_old_covis_nas,re_dmas]):
    for p in priority:
        # Look for matching raw
        for r in raws:
            if p.match(r.host):
                return r
