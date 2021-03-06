import argparse, logging
from pytube import YouTube
from pytube import exceptions

from os import makedirs, getcwd, path
from time import sleep
from sys import argv

def write_subs(channel, video, id, url, subtitles, language):

    with open(path.join("corpus", "raw_subtitles", language, channel, video.title.replace("/", "-") + ".srt"), 'w') as outfile:

        try:
            outfile.write(subtitles.generate_srt_captions())
        except KeyError:
            logging.critical("Video {0}: Could not parse XML for {1} ({2})".format(id, url, video.title))


def get_subs(channel, id, url, language, code):

    try:
        video = YouTube(url)
    except KeyError as e:
        logging.warning("Video {0}: Could not retrieve URL ({1})".format(id, url))
        return 0
    except exceptions.VideoUnavailable as e:
        logging.warning("Video {0}: Video unavailable ({1})".format(id, url))
        return 0
    except:
        logging.critical("Video {0}: An unexpected error occured ({1})".format(id, url))
        return 0


    caption_dict = {caption.name: caption for caption in video.captions}
    print(caption_dict.keys())
    
    for key in caption_dict.keys():

        if language in key:
            if "auto-generated" in language or "auto-generated" not in key:
                write_subs(channel, video, id, url, caption_dict[key], code)
                logging.info("Video {0}: Manual captions found for (URL: {1} Title: {2})".format(id, url, video.title))
                print(key)
                return video.length

    logging.info("Video {0}: No manual captions found (URL: {1} Title: {2})".format(id, url, video.title))
    return 0


def main(args):

    if not path.exists(path.join("corpus", "raw_subtitles", args.code, args.channel)):
        makedirs(path.join("corpus", "raw_subtitles", args.code, args.channel))

    print("Processing videos from channel {0} in language {1}".format(args.channel, args.language))
    if(args.r):
        print("Resuming from video {0}".format(args.r))

    # Metadata
    found_count, total_count, total_time = (0, 0, 0)

    with open(path.join("corpus", "channel_data", args.code, args.file), "r") as video_file:

        for line in list(video_file)[args.r:]:

            url, label = line.strip('\n').split("\t")
            subbed_length = get_subs(args.channel, total_count + args.r, url, args.language, args.code)

            if subbed_length:
                total_time = total_time + subbed_length
                found_count = found_count + 1
                logging.info("Total time (running): {0}".format(total_time))

            total_count += 1
            if total_count % 50 == 0:
                print("Processed {0} URLs...".format(total_count))
                print(found_count, total_count, total_time)

            if(total_count - args.r == args.s):
                break

            # Be considerate!
            sleep(1)

        print("Found {0} subtitled videos (out of {1} videos) totaling {2} seconds".format(found_count, total_count, total_time))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download available manual subtitles from a list of YouTube videos.')

    parser.add_argument('file',     type=str, help='a file containing the URLs')
    parser.add_argument('channel',  type=str, help='a friendly name for the channel')
    parser.add_argument('language', type=str, help='desired output language for the subtitles')
    parser.add_argument('code',     type=str, help='language code')

    parser.add_argument('--r',      type=int, metavar='N', nargs='?', default=0, help='resume downloading from Nth video')
    parser.add_argument('--s',      type=int, metavar='S', nargs='?', default=-1, help='stop after N subtitles')

    parser.add_argument('--log',    action='store_true', default=False, help='log events to file')

    args = parser.parse_args()

    if(args.log):
        logging.basicConfig(filename=(args.channel + '_subtitles.log'),level=logging.DEBUG)

    logging.info("Call: {0}".format(args))
    logging.info("BEGIN DOWNLOAD\n----------")

    main(args)
