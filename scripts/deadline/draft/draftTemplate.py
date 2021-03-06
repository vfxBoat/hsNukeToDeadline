# -*- coding: utf-8 -*-
import sys, os
import Draft
import DraftParamParser
import datetime

from DraftParamParser import ReplaceFilenameHashesWithNumber # For reading frames when encoding

#
#   expectedTypes example
#
#['/Users/frank/Library/Application Support/Thinkbox/Deadline8/slave/lady-rainicorn/jobsData/576ad1fb6333cb65237a2fe6/draftTemplate.py',
# 'username=kimda',
# 'entity=upload_version',
# 'version=draft_v5',
# 'width=1920',
# 'height=1080',
# 'frameList=1000-1005',
# 'startFrame=1000',
# 'endFrame=1005',
# 'inFile=/Volumes/MASTER_02/theboat/testfolder/deadline_test_render/Draft_v5/Draft_v4.####.dpx',
# 'outFile=/Volumes/MASTER_02/theboat/testfolder/deadline_test_render/Draft_v5/Draft/Draft_v4.mov',
# 'outFolder=/Volumes/MASTER_02/theboat/testfolder/deadline_test_render/Draft_v5/Draft',
# 'deadlineJobID=576ad1bd6333cb648c12d0d8',
# 'deadlineRepository=/theboat/_repo',
# 'taskStartFrame=1000',
# 'taskEndFrame=1005'
#]

print "-----------------------"
print "*VFXBOAT "
print "*DAILIES DRAFT TEMPLATE "
print "*v1.1.2 "
print "-----------------------"

expectedTypes = {
    "frameList" : '<string>',
    "inFile"    : '<string>',
    "outFile"   : '<string>',
    "outFolder" : '<string>',
    "width"     : '<string>',
    "height"    : '<string>',
    "version"   : '<string>',
    "entity"    : '<string>',
    "projectRatio"  : '<float>',
    "projectName"   : '<string>',
    "projectDesc"   : '<string>',
    "projectFramerate"      : '<int>',
    "projectCodec"          : '<string>',
    "projectAppendSlate"    : '<string>',
    "projectBurnInInfo"     : '<string>',
    "projectBurnInMask"     : '<string>',
    "projectLut"            : '<string>', # uncomment this to make it obligatory
    "projectOCIOPath"       : '<string>', # uncomment this to make it obligatory
    "projectFramerate" : "<float>"
}
params = DraftParamParser.ParseCommandLine( expectedTypes, sys.argv )
frames = DraftParamParser.FrameRangeToFrames( params.get('frameList') )

inputPath = params.get('inFile')
outWidth = int(params.get('width'))
outHeight = int(params.get('height'))

# Encode the slate frames at the start of the video
toCodec = params.get('projectCodec')
framerate = float(params.get("projectFramerate"))

# Load the LUT
# Supported LUTS by OCIO
#Ext                   Details	Notes
#3dl                   Autodesk Apps: Lustre, Flame, etc. Supports shaper LUT + 3D	Read + Write Support.
#ccc                   ASC CDL ColorCorrectionCollection	Full read support.
#cc 	               ASC CDL ColorCorrection	Full read support.
#csp                   Cinespace (Rising Sun Research) LUT. Spline-based shaper LUT, with either 1D or 3D LUT.	Read + Write Support. Shaper is resampled into simple 1D LUT with 2^16 samples.
#cub                   Truelight format. Shaper Lut + 3D	Full read support.
#cube                  Iridas format. Either 1D or 3D Lut.	Full read support
#hdl                   Houdini. 1D Lut, 3D lut, 1D shaper Lut	Only ‘C’ type is supported. Need to add R G B A RGB RGBA ALL. No support for Sampling tag. Header fields must be in strict order.
#look                  IRIDAS .look	Read baked 3D LUT embedded in file. No mask support.
#mga/m3d               Pandora 3D lut	Full read support.
#spi1d                 1D format. Imageworks native 1D lut format. HDR friendly, supports arbitrary input and output domains	Full read support.
#spi3d                 3D format. Imageworks native 3D lut format.	Full read support.
#spimtx                3x3 matrix + color offset. Imageworks native color matrix format	Full read support.
#vf 	               Inventor 3d lut.	Read support for 3d lut data and global_transform element
lut = None
if params.get("projectLut") is not None:
    ocioConfigPath = params.get("projectOCIOPath") #ex: /theboat/test/_config/config.ocio

    lutName = params.get("projectLut") # Inside the "luts" directory relative to the config.ocio

    print "Using OCIO config from {}".format(ocioConfigPath)
    try:
        Draft.LUT.SetOCIOConfig( ocioConfigPath )

        print "Using LUT {}".format( lutName )
        lut = Draft.LUT.CreateOCIOProcessorFromFile( lutName )
    except:
        print "Unexpected error looking for LUT", sys.exc_info()[0]

        lut = None
        pass

#
# Initialize the video encoder.
#
print "Creating {3} video encoder ({0}x{1} @ {2}fps)".format( outWidth, outHeight, framerate,  toCodec)
# Create a Draft.ImageInfo object used to extract a Draft.Timecode object
imageInfo = Draft.ImageInfo()
firstFile = ReplaceFilenameHashesWithNumber( inputPath, frames[0] )
firstFrame = Draft.Image.ReadFromFile( firstFile, imageInfo )

# If timecode is found, specify the timecode parameter when creating the encoder
print ("The first frame timecode starts at: %s" % imageInfo.timecode)
if (imageInfo.timecode):
    if params['projectAppendSlate'] == "True":
        # If the slate is appended, the initial TC should be one frame less than the actual frame
        firstTimecode = str(imageInfo.timecode).split(":") # "12:40:10:15"
        firstTimecodeHour = firstTimecode[0]
        firstTimecodeMinutes = firstTimecode[1]
        firstTimecodeSeconds = firstTimecode[2]
        firstTimecodeFrames = firstTimecode[3]

        if ( firstTimecodeFrames == "00" ):
            firstTimecodeFrames = str( int(float(framerate)) - 1 )

            if ( firstTimecodeSeconds == "00" ):
                firstTimecodeSeconds = "59"

                if ( firstTimecodeMinutes == "00" ):
                    firstTimecodeMinutes = "59"

                    if ( firstTimecodeHour == "00" ):
                        firstTimecodeHour = "23"
                    else:
                        firstTimecodeHour = str(int(float(firstTimecodeHour)) - 1).zfill(2)
                else:
                    firstTimecodeMinutes = str(int(float(firstTimecodeMinutes)) - 1).zfill(2)
            else:
                firstTimecodeSeconds = str(int(float(firstTimecodeSeconds)) - 1).zfill(2)
        else:
            firstTimecodeFrames = str(int(float(firstTimecodeFrames)) - 1).zfill(2)

        print "This shouldn't make any errors"
        slateTimecode = "%s:%s:%s:%s" % (   str( int( float(firstTimecodeHour)) ).zfill(2)  ,
                                            str( int( float(firstTimecodeMinutes)) ).zfill(2),
                                            str( int( float(firstTimecodeSeconds)) ).zfill(2),
                                            str( int( float(firstTimecodeFrames)) ).zfill(2)  )

        try:
            print "The slate timecode starts at: %s" % slateTimecode
            slateTimecode = Draft.Timecode( slateTimecode )

            # Embed the encoder with the new timecode
            encoder = Draft.VideoEncoder( params['outFile'], fps=framerate, width=outWidth, height=outHeight, quality=100, codec=toCodec , timecode=slateTimecode)
        except:
            print "Error adding timecode ", sys.argv[0]
    else:
        # Embed the encoder with the actual timecode
        encoder = Draft.VideoEncoder( params['outFile'], fps=framerate, width=outWidth, height=outHeight, quality=100, codec=toCodec , timecode=imageInfo.timecode)
else:

    # Dont embed TC
    encoder = Draft.VideoEncoder( params['outFile'], fps=framerate, width=outWidth, height=outHeight, quality=100, codec=toCodec )

#
# Create the anotations
#

# Set text's color and point size
annotationInfo = Draft.AnnotationInfo()
annotationInfo.Color = Draft.ColorRGBA( 1.0,1.0,1.0,1.0 ) # color white
annotationInfo.PointSize = int( outHeight * 0.045 )

#
# Creating the burn in data
#
## For the composite operations
compOperation = Draft.CompositeOperator.OverCompositeOp

if params['projectAppendSlate'] == "True":
    print "Creating the burn in data"
    # Set up the text for the slate frame
    slateText = [("JOB", params["projectName"].replace("%20", " ") ),
                 ("SHOT", params["entity"]),
                 ("VERSION", params['version']),
                 ("FRAMES", params['frameList']),
                 ("ARTIST", params['username']),
                 ("DATE", datetime.datetime.now().strftime("%m/%d/%Y") )]

    slateAbsolutePath = os.path.join('/theboat/_config/scripts/deadline/draft/slateBackground.dpx')
    slateFrame = Draft.Image.ReadFromFile( slateAbsolutePath )

    for i in range( 0, len( slateText ) ):
        txtImg = Draft.Image.CreateAnnotation( slateText[i][0] + ": ", annotationInfo )
        slateFrame.CompositeWithPositionAndAnchor( txtImg, 0.18, 0.7 - (i * 0.06), Draft.Anchor.SouthEast, compOperation )

        txtImg = Draft.Image.CreateAnnotation( slateText[i][1], annotationInfo )
        slateFrame.CompositeWithPositionAndAnchor( txtImg, 0.18, 0.7 - (i * 0.06), Draft.Anchor.SouthWest, compOperation )

    #
    # Create the slate frame
    #
    print "Creating the slate frame"
    # Hold for 1 frame @ 24fps
    #numberOfSlateFrames = 1
    #for i in range( 0, numberOfSlateFrames ):
    encoder.EncodeNextFrame( slateFrame )

#
# Create semi transparent mask
#
if params['projectBurnInMask'] == "True":
    print "Creating semi transparent mask"

    # Create the semi-transparent mask
    ratio = float(params['projectRatio']) # The value 2.35 can be adjusted to fit your project's needs
    maskRectHeight = int( round( ( outHeight - outWidth / ratio ) / 2 ) )
    maskRect = Draft.Image.CreateImage( outWidth, maskRectHeight )
    maskRect.SetChannel( 'A', 0.3 ) # The value 0.3 can be adjusted, higher the value, darker the mask

    mask = Draft.Image.CreateImage( outWidth, outHeight )
    mask.SetChannel( 'A', 0 )

    # Upper mask
    mask.CompositeWithAnchor( maskRect, Draft.Anchor.North, compOperation )
    # Lower mask
    mask.CompositeWithAnchor( maskRect, Draft.Anchor.South, compOperation )

# progress calculation var
progressCounter = 0
lastPercentage = -1

#
# Mask Anotations
#
if params['projectBurnInInfo'] == "True":
    annotationInfo.Color = Draft.ColorRGBA( 1.0, 1.0, 1.0, 1.0 )
    annotationInfo.PointSize = int( outHeight * 0.020 ) # font size
    #annotationInfo.FontType = "Helvetica"
    annotationOffset = int( outHeight * 0.020 )*2;

    # Anchor Points
    northWest = {"x" : annotationOffset, "y" : annotationOffset}
    southWest = {"x" : annotationOffset, "y" : outHeight-annotationOffset}
    northEast = {"x" : outWidth - annotationOffset, "y" : annotationOffset}
    southEast = {"x" : outWidth - annotationOffset, "y" : outHeight-annotationOffset}

    # North West annotation
    projectNameAndDateAnnotation = Draft.Image.CreateAnnotation( params['projectName'].replace("%20", " ") +"\n"+ datetime.datetime.now().strftime("%m/%d/%Y"), annotationInfo)

    # North East annotation
    studioNameAnnotation = Draft.Image.CreateAnnotation( "VFXBOAT", annotationInfo ) # we should put the logo here

    # South West annotation
    # filaname - size => this annotation is made in the for loop
    descriptionAnnotation = Draft.Image.CreateAnnotation( params['projectDesc'].replace("%20", " ") , annotationInfo)

    # South East annotation
    # frame number => this annotation is made up in the for loop
    artistAnnotation = Draft.Image.CreateAnnotation( params['username'], annotationInfo )

#
# Processing the input images
#
print "Processing the input images"

for frameNum in frames:
    inFile = ReplaceFilenameHashesWithNumber( inputPath, frameNum )
    frame = Draft.Image.ReadFromFile( inFile )

    # Resize the frame if bigger than the out file size
    originalWidth = frame.width
    originalHeight = frame.height

    # Apply the LUT
    if lut is not None:
        print "Applying Lut"
        lut.Apply(frame)
    else:
        print "No Lut to apply"

    if frame.width != outWidth or frame.height != outHeight:
        print "WARNING: Resizing image from {0}x{1} to {2}x{3}".format( frame.width, frame.height, outWidth, outHeight )
        frame.Resize( outWidth, outHeight )

    if params['projectBurnInMask'] == "True":
        # Add the semi-transparent mask
        print "Add the semi-transparent mask"
        frame.Composite( mask, 0, 0, compOperation )

    if params['projectBurnInInfo'] == "True":
        # Add burn ins
        # North West
        print "Add burn ins: North West"
        frame.CompositeWithAnchor( projectNameAndDateAnnotation , Draft.Anchor.NorthWest, compOperation )

        # North East
        print "Add burn ins: North East"
        frame.CompositeWithAnchor( studioNameAnnotation  , Draft.Anchor.NorthEast, compOperation )

        # South West annotation
        print "Add burn ins: South West"
        filenameAndSizeAnnotation = Draft.Image.CreateAnnotation( ("%s - %sx%s\n" % (inFile, originalWidth, originalHeight)), annotationInfo ) # added a \n for line break
        frame.CompositeWithAnchor( filenameAndSizeAnnotation, Draft.Anchor.SouthWest, compOperation )
        frame.CompositeWithAnchor( descriptionAnnotation , Draft.Anchor.SouthWest, compOperation )

        # South East annotation
        print "Add burn ins: South East"
        frameNumAnnotation = Draft.Image.CreateAnnotation( ("%s\n" % (frameNum) ), annotationInfo ) # added a \n for line break
        frame.CompositeWithAnchor( frameNumAnnotation  , Draft.Anchor.SouthEast, compOperation )
        frame.CompositeWithAnchor( artistAnnotation  , Draft.Anchor.SouthEast, compOperation )

    encoder.EncodeNextFrame( frame )

    progressCounter = progressCounter + 1
    percentage = progressCounter * 100 / len( frames )

    if percentage != lastPercentage:
        lastPercentage = percentage
        print "Encoding Progress: {0}%".format( percentage )

print "Finalizing encoding..."
encoder.FinalizeEncoding()
print "Done!"
