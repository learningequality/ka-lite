
def generate_all_paths(path, base_path="/"):

    if base_path[-1:] != "/":   # Must have trailing slash to work.
        base_path += "/"
    if path[-1:] == "/":        # Must NOT have trailing slash to work.
        path = path[0:-1]
        
    all_paths = []
    cur_path = base_path[0:-1]
    for dir in path[len(base_path)-1:].split("/"): # start AFTER the base path
        cur_path = cur_path + dir + "/"
        all_paths.append(cur_path)
    return all_paths

if __name__=="__main__":
    print generate_all_paths("/test/me/out")
    print generate_all_paths("/test/me/out/")
    print generate_all_paths("/test/me/out", base_path="/test")
    