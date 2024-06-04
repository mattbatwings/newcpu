# Display error message
def fatal_error(origin, message):
    exit(f"{origin}: fatal error: {message}")
#
def find_nz(string:str, delimiter:str, start:int=0):
    output=str.find(string, delimiter, start)
    if(output==-1):
        return output+len(string)+1
    else:
        return output
# str.find() but with multi-delimiter support
def strfind(string, delimiters, start=0):
    output=[]
    idx=start
    try:
        while(string[idx] not in delimiters):
            idx += 1
    except IndexError:
        return -1
    return idx
# inverted ffind()
def inverted_strfind(string, delimiters, start=0):
    output=[]
    idx=start
    try:
        while(string[idx] in delimiters):
            idx += 1
    except IndexError:
        return -1
    return idx
# str.split() but with multi-delimiter support
def split_string(string:str, delimiters:str):
    idx=0
    output=[]
    while(idx<len(string)):
        idx=inverted_strfind(string, delimiters, idx)
        if(idx==-1):
            break
        idx_end=strfind(string, delimiters, idx)
        if(idx_end==-1):
            output.append(string[idx:])
            break
        output.append(string[idx:idx_end])
        idx=idx_end
    return output
