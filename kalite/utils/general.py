
def break_into_chunks(bigiterator, chunksize=500):
    biglist = list(bigiterator)
    return [biglist[i:i+chunksize] for i in range(0, len(biglist), chunksize)]
