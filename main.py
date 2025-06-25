import time
#import face_utils
import inotify.adapters


def main():
    # face_utils.check_face_camera()
    
    file_to_watch = '/home/Fox/code/WTF_Security_Lock/'

    i = inotify.adapters.Inotify()
    i.add_watch('{}'.format(file_to_watch))

    print("Listening for events in {}".format(file_to_watch))
    for event in i.event_gen(yield_nones=False):
        (_, event_types, path, filename) = event
        if 'IN_ACCESS' in event_types:
            print(f"🔔 目录访问了: {path}")
        elif 'IN_OPEN' in event_types:
            print(f"📂 目录被打开: {path}")


if __name__ == '__main__':
    main()
