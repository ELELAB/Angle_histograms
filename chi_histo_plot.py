import numpy as np
import matplotlib.pyplot as plt
import glob
import re
import matplotlib as mpl

__date__ = "2017_11_02"
__author__ = "Mads Nygaard"


# A key to sort after numbers in the string
def natural_n_first_sort_key(s, _nsre=re.compile('[a-z]{3}\d?[A-Z0-9]{3}(\d+)')):
    numbers = 0
    templist = []
    for text in re.split(_nsre, str(s)):
        if text.isdigit():
            templist.insert(numbers, int(text))
            numbers += 1
        else:
            templist.append(text.lower())
    return templist


def xmgdatgen(fname):
    return np.genfromtxt((r for r in open(fname) if not r[0] in ('@', '#')))


def hisColum(filelists, labels=None, bins=36.0, figsize=(11.96, 6), njumps=11, gshift=0, align=None):
    """Takes ((file1_1,file1_2,..),(file2_1,file2_2,..),..) and plots 
    histograms of file1* over file2* over ...
    njumps: coarse-grainedness of the time-coloring
    bins: number of bins in histogram
    shift: shift of residuenumber in the label"""

    # Setting up the figure
    n_cols = len(max(filelists, key=lambda x: len(x)))
    n_rows = len(filelists)
    fig, doubaxlist = plt.subplots(n_rows, n_cols, sharex=True,
                                   sharey=False, figsize=figsize)
    fig.subplots_adjust(top=0.98, bottom=0.10, right=0.98, left=0.08,
                        hspace=0.09, wspace=0.09)
    if n_rows == 1:  # Wrap in list if only one folder
        doubaxlist = np.array((doubaxlist,))

    # Setting parameters
    binwidth = 360.0/bins
    binrange = np.arange(-180, 180 + binwidth, binwidth)
    cmap = plt.get_cmap("viridis_r")
    rowcount = 0
    
    if labels is None:
        labels = [None]*n_rows

    for axlist, filelist, label in zip(doubaxlist, filelists, labels):
        rowcount += 1
        colcount = 0
        if label is not None:
            axlist[0].set_ylabel(label)
        for ax, fname in zip(axlist, filelist):
            colcount += 1
            if rowcount is n_rows:
                ax.set_xlabel("Degrees")
            print rowcount, colcount
            if fname is not None and fname is not '-':
                data = xmgdatgen(fname)  # Loading data
                data, mintime, maxtime = data[:, 1], data[0, 0], data[-1, 0]
                datalen = len(data)
                jumplen = datalen//njumps
                # Going through data "backwards"
                for idx, n in zip(reversed(range(njumps)),
                                  range(datalen, 0, -jumplen)):
                    ax.hist(data[0:n], bins=binrange, color=cmap(idx/float(njumps-1)))
            
                # Getting a label 
                reg = re.search("([a-z]{3,})(\d?)([A-Z0-9]{3})(\d+)", fname)             
                text = r"$\%s%s$,%s$^{%s}$" % (reg.group(1), reg.group(2),
                                               reg.group(3), int(reg.group(4))+int(gshift))
            else:
                data = []
                mintime = np.float64(0)
                maxtime = np.float64(0)
                if fname == '-':
                    text = '-'
                else:
                    text = ""
            ax.text(0.05, 0.8, text, transform=ax.transAxes, size=10)  # Adding the label 
    
    # Pretty x_axis for degrees
    plt.xlim([-180, 180])
    plt.gca().get_xaxis().set_ticks([-180, -90, 0, 90, 180])
    plt.gca().get_xaxis().set_ticklabels(["", -90, 0, 90, ""])
    
    # Adding a colorbar
    pad = 0.12
    cax, kw = mpl.colorbar.make_axes([ax for ax in doubaxlist.flat],
                                     orientation='horizontal', fraction=0.04,
                                     pad=pad) 
    norm = mpl.colors.Normalize(vmin=mintime/1000000.0, vmax=maxtime/1000000.0)
    cb1 = mpl.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm,
                                    orientation='horizontal')
    cb1.set_label(r"Time [$\mu$s]")


def combined_plot(dir_names, n=11, angles=["phi", "psi", "chi1"],
                  resids="all", restypes="all", **kwargs):
    """Helper function for hisColum. Plots 'angles' from 'dir_names'.
    (Only good for up to ~15 residues.)
    """
    def l_to_regex(l, minlen, num=False):
        if type(l) is list:
            return "("+"|".join(map(lambda x: x.upper(), l))+")"
        elif l.lower() == "all":
            if num is False:
                end = "}"
            else:
                end = ",}"
            return "[A-Z0-9]"+"{"+str(minlen)+end 
        elif l.isalpha():
            return l.upper()
        elif l.isdigit():
            return l
        else:
            raise ValueError("Cannot convert %s" % l)

    def __readAlign(fname):
        a_dict = {}
        with open(fname, "r") as f:
            for line in f.readlines():
                l = line.split('\t')
                a_dict[l[0]] = l[1].strip()
        return a_dict
    
    def __inthelist(reg, flist):
        k = 0
        while(k < len(flist) and not re.match(reg, flist[k])):
            k += 1
        return k
    #-------------------------------------------
    try:
        alignment = __readAlign(kwargs['align'])
        aln = True
    except IOError:
        aln = False
    
    if type(angles) is str:
        angles = [angles]

    for angle in angles:
        print angle
        list_of_filelist = []
        for lshift, label, loc in dir_names:
            if type(resids) == str:
                resids_shift = resids
            else:
                resids_shift = map(lambda x: str(int(x)+int(lshift)), resids)
            flist = sorted(glob.glob(loc + "/" + angle + "*.xvg"), key=natural_n_first_sort_key)
            regex_str = r""+loc+".*"+angle+l_to_regex(restypes, 3) +\
                        l_to_regex(resids_shift, 1, num=True)+"\.xvg"
            filtered_list = [x for x in flist if re.match(regex_str, x) is not None]
            if aln:
                new_list_of_files = []
                db = 0
                for i, r in enumerate(alignment[label]):
                    if r == '-':
                        new_list_of_files.append('-')
                        db += 1
                    else:
                        j = str(i-db+1)
                        regex_res = r""+loc+".*"+angle+l_to_regex(restypes, 3)+j+"\.xvg"
                        w = __inthelist(regex_res, filtered_list)
                        if w < len(filtered_list):  # in the filtered_list
                            new_list_of_files.append(filtered_list[w])
                        else:
                            new_list_of_files.append(None)
            else:
                new_list_of_files = filtered_list

            list_of_filelist.append(new_list_of_files)

        #check if both are None in the same position then delete them!
        k = 0
        while(k < len(list_of_filelist[0])):
            l = 0
            while(l < len(list_of_filelist) and list_of_filelist[l][k] is None):
                l += 1
            if(l >= len(list_of_filelist)):
                for l in range(len(list_of_filelist)):
                    del list_of_filelist[l][k]
            k += 1

#        print list_of_filelist
        n = 10         
        l = [zip(*list_of_filelist)[i:i + n] for i in xrange(0, len(zip(*list_of_filelist)), n)]
#        break
         
        for idx, p in enumerate(l):
            hisColum(zip(*p), labels=zip(*dir_names)[1], **kwargs)
            plt.savefig(angle + "%s_%s.pdf" % (idx*n+1, idx*n+n))
            plt.close()


if __name__ == "__main__":
    import ConfigParser
    import tempfile
    import argparse
    import os

    class ListConfigParser(ConfigParser.SafeConfigParser):
        """Modified ConfigParser to read configfile with lists"""
        def listread(self, fname):
            """Reads a config with a list under [Folders] tag"""
            self.dirs = []  # For the list of folders with labels
            tfile = tempfile.TemporaryFile()
            with open(fname, "r") as f:
                for line in f.readlines():
                    if "[Folders]" in line.strip():
                        folderlist = True
                        continue
                    elif "[" in line.strip():
                        folderlist = False
                        tfile.write(line)
                    # Sort out blank lines and comments
                    elif folderlist is True and line.strip() is not "" and not line.startswith("#"):  
                        if len(line.strip().split()) == 1:  # If no label, put in group 0
                            self.dirs.append(tuple(0, line.strip()))
                        elif len(line.strip().split()) >= 2:
                            self.dirs.append(tuple(line.strip().split()))
                    elif folderlist is False:  # Parse the rest to a tempfile for standard configparser
                        tfile.write(line)
            tfile.seek(0)  # Read tempfile from line 0
            self.readfp(tfile)
            return self.getlist()

        def listwrite(self, f):
            """Writes the config to the file f including the list"""
            if len(self.dirs) > 0:
                f.write("[Folders]\n")
                f.writelines(self.forprint(self.dirs))
                f.write("")
            self.write(f)

        def forprint(self, alist):
            newlist = []
            for n in alist:
                newlist.append(" ".join(n)+"\n")
            return newlist

        def appendfolder(self, dirname):
            """Append to the list"""
            self.dirs.append(dirname+"\n")

        def getlist(self):
            """Gets the list cleaned"""
            return self.dirs
    
    def hyphen_range(s):
        """ Takes a range in form of "a-b" and generate a list of numbers 
        between a and b inclusive. Also accepts comma separated ranges like 
        "a-b,c-d,f" will build a list which will include Numbers from a to 
        b, a to d and f"""
        s = "".join(s.split())  # removes white space
        r = set()
        for x in s.split(','):
            t = x.split('-')
            if len(t) not in [1, 2]:
                raise SyntaxError("hash_range is given its arguement as "+s+" which seems not correctly formated.")
             
            if len(t) == 1: 
                r.add(int(t[0]))
            else: 
                r.update(set(range(int(t[0]), int(t[1])+1)))
        l = list(r)
        l.sort()
        return l

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=("You need to run gmx chi first to generate the input-files. Something like:\n"
                                                  "gmx_mpi chi -s $conf -f $traj -phi -psi -omega -all -maxchi 6"))

    parser.add_argument("-f", metavar="config.cfg", default="config.cfg",
                        help="Specify the input config file")
    parser.add_argument("-align", metavar="align.aln", default="align.aln", help="Specify the input alignment file like: label1 sequence with gaps(-) next line label2...")
    
    args = parser.parse_args()    

    config = ListConfigParser()
    config.listread(args.f)
    groupfolderlist = config.getlist()

    settings = {"resids": "all", "angles": ["phi", "psi", "chi1"], 
                "restypes": "all", "n": 11, "gshift": 0}

    for key in sorted(settings.keys()):
        try:
            option = config.get("Settings", key)
            print key, option
            if key is "resids":
                try:
                    settings[key] = [str(x) for x in hyphen_range(option)]
                except ValueError:
                    if option.lower() == "all":
                        pass
                    else:
                        raise
            elif "," in option:
                settings[key] = map(lambda s: s.strip(), option.split(",")) 
            else: 
                settings[key] = option
        except ConfigParser.NoOptionError:
            print("No setting for '"'%s'"' found, "
                  "will use default: %s" % (key, settings[key]))
    
    # Test if folders exists 
    for single_folder in zip(*groupfolderlist)[2]:
        if not os.path.isdir(single_folder):
            print "Cannot find folder %s" % (single_folder) 
            missing_folder = True

    #if missing_folder is True:
    #    raise IOError("Some folders/files not found")
    
    combined_plot(groupfolderlist, n=settings["n"], angles=settings["angles"],
                  restypes=settings["restypes"], resids=settings["resids"],
                  gshift=settings["gshift"], align=args.align)

    #SORT resids
"""
# Add folders here:
folders = ["./C22st_unPhos_mod1/",
           "./C22st_S1043p_mod1/"]

# Run plot, specify the res-num shift (if any) and angles if other than "default"
combined_plot(folders, shift=200)

# A more manual way is shown below.
# e.g. if more than 10-15 angles are needed to be plot it is an idea
# to do some slicing of the lists and plot in seperate plots

phi1 = sorted(glob.glob("./C22st_unPhos_mod1/phi*.xvg"), key=natural_n_first_sort_key)
psi1 = sorted(glob.glob("./C22st_unPhos_mod1/psi*.xvg"), key=natural_n_first_sort_key)
chi1 = sorted(glob.glob("./C22st_unPhos_mod1/chi1*.xvg"), key=natural_n_first_sort_key)
phi2 = sorted(glob.glob("./C22st_S1043p_mod1/phi*.xvg"), key=natural_n_first_sort_key)
psi2 = sorted(glob.glob("./C22st_S1043p_mod1/psi*.xvg"), key=natural_n_first_sort_key)
chi2 = sorted(glob.glob("./C22st_S1043p_mod1/chi1*.xvg"), key=natural_n_first_sort_key)



hisColum((phi1, phi2))
plt.savefig("Phi_2.pdf")

hisColum((chi1, chi2))
plt.savefig("Chi_2.pdf")

hisColum((psi1, psi2))
plt.savefig("Psi_2.pdf")
"""
