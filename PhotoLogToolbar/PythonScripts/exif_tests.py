from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS, IFD
#from pillow_heif import register_heif_opener
#import pillow_avif  

#register_heif_opener()

def print_exif(fname: str):
    img = Image.open(fname)
    exif = img.getexif()

    print('>>>>>>>>>>>>>>>>>>', 'Base tags', '<<<<<<<<<<<<<<<<<<<<')
    for k, v in exif.items():
        tag = TAGS.get(k, k)
        print(tag, v)

    for ifd_id in IFD:
        print('>>>>>>>>>', ifd_id.name, '<<<<<<<<<<')
        try:
            ifd = exif.get_ifd(ifd_id)

            if ifd_id == IFD.GPSInfo:
                resolve = GPSTAGS
            else:
                resolve = TAGS

            for k, v in ifd.items():
                tag = resolve.get(k, k)
                print(tag, v)
        except KeyError:
            pass

if __name__ == '__main__':
    print_exif("C:\\Code\\ArcMap Extensions\\Photo-Log Toolbar\\Test Projects\\200702227 - Hardesty\\2012-06-05 - Site Visit\\Photographs\\DSC00664.JPG")
    print_exif("C:\\Code\\ArcMap Extensions\\Photo-Log Toolbar\\Test Projects\\201500307 - Putah Creek Cram Day 2\\2016-08-23 - Site visit\\Photographs\\DSCN0874.JPG")
    print(' ')