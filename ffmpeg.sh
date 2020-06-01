#!/bin/bash
# run in a loop - because sometimes ffmpeg loses connection to the RTSP stream
while :
do
  ffmpeg -fflags nobuffer \
   -rtsp_transport udp \
   -i rtsp://roocell:Garagewyze@192.168.1.236/live \
   -vsync 0 \
   -copyts \
   -vcodec copy \
   -an \
   -movflags frag_keyframe+empty_moov \
   -an \
   -hls_flags delete_segments \
   -f segment \
   -segment_list_flags live \
   -segment_wrap 2 \
   -segment_time 0.5 \
   -segment_list_size 1 \
   -segment_format mpegts \
   -segment_list /home/pi/garage-pi/video/garage.m3u8 \
   -segment_list_type m3u8 \
   -segment_list_entry_prefix /video/ \
   /home/pi/garage-pi/video/%3d.ts

	sleep 1
done
