# By Mostapha Sadeghipour Roudsari
# Sadeghipour@gmail.com
# Honeybee started by Mostapha Sadeghipour Roudsari is licensed
# under a Creative Commons Attribution-ShareAlike 3.0 Unported License.

"""
Read the results of the annual study for a single hour of the year

-
Provided by Honeybee 0.0.51

    Args:
        _illFilesAddress: List of .ill files
        _testPoints: List of 3d Points
        _annualProfiles: Address to a valid *_intgain.csv generated by daysim.
        _HOY: Hour of the year
    Returns:
        iIllumLevelsNoDynamicSHD: Illuminance values without dynamic shadings
        iIllumLevelsDynamicSHDGroupI: Illuminance values when shading group I is closed
        iIllumLevelsDynamicSHDGroupII: Illuminance values when shading group II is closed
        iIlluminanceBasedOnOccupancy: Illuminance values based on Daysim user behavior
        shadingGroupInEffect: 0: no blind, 1: shading group I, 2: shading group II
"""
ghenv.Component.Name = "Honeybee_Read Hourly Results from Annual Daylight Study"
ghenv.Component.NickName = 'readDSHourlyResults'
ghenv.Component.Message = 'VER 0.0.51\nFEB_24_2014'
ghenv.Component.Category = "Honeybee"
ghenv.Component.SubCategory = "4 | Daylight | Daylight"
try: ghenv.Component.AdditionalHelpFromDocStrings = "0"
except: pass



import os
from System import Object
import Grasshopper.Kernel as gh
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path


def sortIllFiles(illFilesAddress):
    sortedIllFiles = []
    for shadingGroupCount in range(illFilesAddress.BranchCount):
        fileNames = list(illFilesAddress.Branch(shadingGroupCount))
        try:
            fileNames = sorted(fileNames, key=lambda fileName: int(fileName.split(".")[-2].split("_")[-1]))
            sortedIllFiles.append(fileNames)
        except:
            tmpmsg = "Can't sort the files based on the file names. Make sure the branches are sorted correctly."
            w = gh.GH_RuntimeMessageLevel.Warning
            ghenv.Component.AddRuntimeMessage(w, tmpmsg)
    
    # sort shading states inside sortedIllFiles
    illFileSets = {}
    for listCount, fileNames in enumerate(sortedIllFiles):
        try:
            if len(fileNames[0].split("_state_"))==1:
                illFileSets[0] = fileNames
            else:
                key = int(fileNames[0].split("_state_")[1].split("_")[0])-1
                illFileSets[key] = fileNames
        except Exception, e:
            print "sortinng the branches failed!"
            illFileSets[listCount] = fileNames
    
    return illFileSets

def main(illFilesAddress, testPoints, HOY, annualProfiles):
    msg = str.Empty
    
    shadingProfiles = []
    
    #groups of groups here
    for resultGroup in  range(testPoints.BranchCount):
        shadingProfiles.append([])
    
    # print len(shadingProfiles)
    if len(annualProfiles)!=0:
        # check if the number of profiles matches the number of spaces (point groups)
        if testPoints.BranchCount!=len(annualProfiles):
            msg = "Number of annual profiles doesn't match the number of point groups!\n" + \
                  "NOTE: If you have no idea what I'm talking about just disconnect the annual Profiles\n" + \
                  "In that case the component will give you the results with no dynamic shadings."
            return msg, None, None
        
        # sort the annual profiles
        try:
            annualProfiles = sorted(annualProfiles, key=lambda fileName: int(fileName.split(".")[-2].split("_")[-1]))
        except:
            pass
            
        # import the shading groups
        # this is a copy-paste from Daysim annual profiles
        for branchCount in range(len(annualProfiles)):
            # open the file
            filePath = annualProfiles[branchCount]
            with open(filePath, "r") as inf:
                for lineCount, line in enumerate(inf):
                    if lineCount == 3:
                        headings = line.strip().split(",")[3:]
                        resultDict = {}
                        for heading in range(len(headings)):
                            resultDict[heading] = []
                    elif lineCount> 3:
                        results = line.strip().split(",")[3:]
                        for resCount, result in enumerate(results):
                            resultDict[resCount].append(float(result))
                            
                shadingCounter = 0
                for headingCount, heading in enumerate(headings):
                    if heading.strip().startswith("blind"):
                        shadingProfiles[branchCount].append(resultDict[headingCount])
                        shadingCounter += 1
        # make sure number of ill files matches the number of the shading groups
        # and sort them to work together
        for shadingProfile in shadingProfiles:
            if len(shadingProfile)!= illFilesAddress.BranchCount - 1:
                msg = "Number of annual profiles doesn't match the number of shading groups!\n" + \
                      "NOTE: If you have no idea what I'm talking about just disconnect the annual Profiles\n" + \
                      "In that case the component will give you the results with no dynamic shadings."
                return msg, None, None
            else:
                # looks right so let's sort them
                # sort each list inside the branch and took the first one for sorting the branches!
                illFileSets = sortIllFiles(illFilesAddress)

                    
    elif illFilesAddress.BranchCount > 1 and illFilesAddress.BranchCount-1 != len(annualProfiles):
        tempmsg = "Annual profile files are not provided.\nThe result will be only calculated for the original case with no blinds."
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, tempmsg)
        # copy the files into the 
        illFileSets = sortIllFiles(illFilesAddress)
    else:
        # no profile
        illFileSets = sortIllFiles(illFilesAddress)
        
    # read the data for hour of the year and multiply it with the shading
    numOfPts = testPoints.DataCount
    
    # 3 place holderd for the potential 3 outputs
    # no blinds, shading group I and shading group II
    illuminanceValues = {0: [],
                         1: [],
                         2: [],
                         }
    
    totalPtCount = 0
    ptsCountSoFar = 0
    for shadingGroupCount in range(len(illFileSets.keys())):
        for resultFile in illFileSets[shadingGroupCount]:
            result = open(resultFile, 'r')
            for lineCount, line in enumerate(result):
                if lineCount == int(HOY-1):
                   line = line.replace('\n', '', 10)
                   lineSeg = line.Split(' ')
                   for hourLuxValue in lineSeg[4:]:
                      illuminanceValues[shadingGroupCount].append(float(hourLuxValue))
            result.close()

    return msg, illuminanceValues, shadingProfiles


if _HOY!=None and _illFilesAddress.DataCount!=0 and _illFilesAddress.Branch(0)[0]!=None and _testPoints:
    
    _testPoints.SimplifyPaths()
    _illFilesAddress.SimplifyPaths()
    
    numOfPtsInEachSpace = []
    for branch in range(_testPoints.BranchCount):
        numOfPtsInEachSpace.append(len(_testPoints.Branch(branch)))
    
    msg, illuminanceValues, shadingProfiles = main(_illFilesAddress, _testPoints, _HOY, annualProfiles_)

    if msg!=str.Empty:
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, msg)
        
    else:
        iIllumLevelsNoDynamicSHD = DataTree[Object]()
        iIllumLevelsDynamicSHDGroupI = DataTree[Object]()
        iIllumLevelsDynamicSHDGroupII = DataTree[Object]()
        iIlluminanceBasedOnOccupancy = DataTree[Object]()
        
        # now this is the time to create the mixed results
        # I think I confused blind groups and shading states at some point or maybe I didn't!
        # Fore now it will work for one shading with one state. I'll check for more later.
        
        blindsGroupInEffect = 0
        # for each space
        for spaceCount in range(len(numOfPtsInEachSpace)):
            p = GH_Path(spaceCount)
            iIllumLevelsNoDynamicSHD.AddRange(illuminanceValues[0][sum(numOfPtsInEachSpace[:spaceCount]):sum(numOfPtsInEachSpace[:spaceCount+1])], p)
            
            if len(illuminanceValues[1])!=0 and shadingProfiles[spaceCount]!=[]:
                
                if shadingProfiles[spaceCount][0][_HOY-1] == 1: blindsGroupInEffect = 1
                iIllumLevelsDynamicSHDGroupI.AddRange(illuminanceValues[1][sum(numOfPtsInEachSpace[:spaceCount]):sum(numOfPtsInEachSpace[:spaceCount+1])], p)
                
            if len(illuminanceValues[2])!=0 and shadingProfiles[spaceCount]!=[]:
                if shadingProfiles[spaceCount][1][_HOY-1] == 1: blindsGroupInEffect = 2
                iIllumLevelsDynamicSHDGroupII.AddRange(illuminanceValues[2][sum(numOfPtsInEachSpace[:spaceCount]):sum(numOfPtsInEachSpace[:spaceCount+1])], p)
                

            iIlluminanceBasedOnOccupancy.AddRange(illuminanceValues[blindsGroupInEffect][sum(numOfPtsInEachSpace[:spaceCount]):sum(numOfPtsInEachSpace[:spaceCount+1])], p)
            
            shadingGroupInEffect =  blindsGroupInEffect

