from Utils import Error,logger
import math
import sys

_logger=logger().getLogger('Interface')
class Result:
    UNDEFINED = "UNDEFINED"
    FAILED = "FAILED"
    NOTPASSED = "NOTPASSED"
    SUCCESS = "SUCCESS"

class Output:
    """
    Class representing the result of a test
    """
    def __init__(self,name,failedThreshold=0.05,passedThreshold=0.90,logx=False,logy=False):
        """
        Create an output class, with thresholds for failed and passed.
        """
        self.name = name
        self.low = failedThreshold
        self.high= passedThreshold
        self.logx = logx
        self.logy = logy
        self.result = Result.UNDEFINED
        self.value = None
    def checkResult(self,result):
        """
        Check result against thresholds:
        result < failedThreshold -> FAILED
        result >= passedThreshold -> SUCCESS
        else -> NOTPASSED
        """
        self.value = result
        if result < self.low:
            self.result = Result.FAILED
        elif result < self.high:
            self.result = Result.NOTPASSED
        else:
            self.result = Result.SUCCESS
    def pprint(self,stream,colors=True):
        class bcolors:
            HEADER = '\033[95m'
            OKBLUE = '\033[94m'
            OKGREEN = '\033[92m'
            WARNING = '\033[93m'
            FAIL = '\033[91m'
            ENDC = '\033[0m'
            def disable(self):
                self.HEADER = ''
                self.OKBLUE = ''
                self.OKGREEN = ''
                self.WARNING = ''
                self.FAIL = ''
                self.ENDC = ''
        bc = bcolors()
        if not colors:
            bc.disable()
        msg = "%s : "%self.name.rjust( 35 )
        retcode=0
        if self.result == Result.FAILED:
            retcode=1
            msg += bc.FAIL
        elif self.result == Result.NOTPASSED:
            msg += bc.WARNING
        elif self.result == Result.SUCCESS:
            msg += bc.OKGREEN
        msg += self.result.ljust( 10 )
        msg += bc.ENDC
        stream.write(msg)
        return retcode

    def __str__(self):
        return "%s : %s"%(self.name,self.result)

class Algorithm:
    """
    Class performing the execution of a test and
    setting the Output value
    """
    def __init__(self,test=None,output=None):
        """
        Create an Algorithm from test and output.
        test should implement the value() function.
        output must implement the checResukt(...) function
        """
        self.test = test
        self.output = output
    def check(self):
        """
        Executes test and set output value
        """
        from Tests import SkipTest
        try:
            val = self.test.value()
            self.output.checkResult( val )
        except SkipTest:
            #Test should be simply skipped
            val = 'undef'
        _logger.info(' Algorithm.check() -> %s for %s : %s (%s)'%(
            self.test.__class__.__name__,
            self.output.name,
            str(val),
            self.output.result))
        return self.output.result

class ConfigurationError(Error):
    def __init__(self,msg):
        Error.__init__(self,"Configuration Error: %s"%msg)
        
from Utils import SplitLine 
class Configuration:
    """
    """
    BINNEDKEY = 'Binned'
    UNBINNEDKEY = 'UnBinned'
    HISTOSKEY = 'Histos'
    DATASETKEY= 'DataSet'
    DEFAULTTESTKEY = 'DefaultTestName'
    DEFAULTREFKEY = 'DefaultReferenceFile'
    DEFAULTTHRESHOLDSKEY = 'DefaultThresholds'
    NAMEKEY = 'Name'
    REFERENCEKEY = 'ReferenceFile'
    TESTNAMEKEY = 'TestName'
    THRESHOLDSKEY = 'Thresholds'
    LOGXKEY = 'LogX'
    LOGYKEY = 'LogY'
    TYPEKEY = 'Type'
    SIZEKEY = 'Size'
    ELEMENTKEY = 'Element'
    TEXTKEY = 'Text'
    LINESKEY = 'Lines'
    WORDSKEY = 'Words'
    VALUECOLKEY = 'ValueCol'
    VALUEREFKEY = 'ValueRef'
    VALUEKEY = 'Value'
    ERRORCOLKEY = 'ErrorCol'
    ERRORREFKEY = 'ErrorRef'
    ERRORKEY = 'Error'
    ERRORTYPEKEY = 'ErrorType'
    def __init__(self,confile):
        _logger.debug('Creating Configuration instance for file: %s'%confile)
        self.filename = confile
        self.configuration = {}
        try:
            execfile( confile , self.configuration )
        except Exception,e:
            raise ConfigurationError("Error reading configuration file %s: %s"%(self.filename,str(e)))

    def parseAndCheckText(self):
        """
        Check configuration for Binned distributions
        """
        _logger.debug("Checking configuration syntax for 'Text'")
        if not self.configuration.has_key(Configuration.TEXTKEY):
            _logger.debug("No 'Binned' configuration, nothing to do")
            return
        self.text=self.configuration[Configuration.TEXTKEY]
        if type(self.text)!=type(dict()):
            raise ConfigurationError("Text block should be of type dict")
        #If not specified, add defaults placeholders
        if not self.text.has_key(Configuration.DEFAULTTESTKEY):
            self.text[Configuration.DEFAULTTESTKEY]=None
        if not self.text.has_key(Configuration.DEFAULTREFKEY):
            self.text[Configuration.DEFAULTREFKEY]=None
        if not self.text.has_key(Configuration.DEFAULTTHRESHOLDSKEY):
            self.text[Configuration.DEFAULTTHRESHOLDSKEY]=None
        else:
            if type(self.text[Configuration.DEFAULTTHRESHOLDSKEY])!=type(list()) or \
                len(self.text[Configuration.DEFAULTTHRESHOLDSKEY])!=2:
                raise ConfigurationError("Thresholds should be a list of size 2")
        if not self.text.has_key(Configuration.LINESKEY):
            raise ConfigurationError("Text block should have a %s variable"%Configuration.LINESKEY)
        if type(self.text[Configuration.LINESKEY])!=type(list()):
            raise ConfigurationError("%s variable should be of type list"%Configuration.LINESKEY)
        if len(self.text[Configuration.LINESKEY])==0:
            raise ConfigurationError("Text variable should contain at least one dictionary")
        for elem in self.text[Configuration.LINESKEY]:
            if type(elem)!=type(dict()):
                raise ConfigurationError("Text element %s should be of type dictionary"%elem)
            if elem.has_key(Configuration.THRESHOLDSKEY):
                if type(elem[Configuration.THRESHOLDSKEY])!=type(list()) or \
                    len(elem[Configuration.THRESHOLDSKEY])!=2:
                    raise ConfigurationError("Thresholds should be a list of size 2")
            if not elem.has_key(Configuration.WORDSKEY):
                raise ConfigurationError("Text element %s should have at least %s key"%(elem,Configuration.WORDSKEY))
#            if elem.has_key(Configuration.WORDSKEY):
#                if type(elem[Configuration.WORDSKEY])!=type(list()) :
# or \
#                    len(elem[Configuration.WORDSKEY])%2!=2:
#                    raise ConfigurationError(Words should be a list of size even")
            if not elem.has_key(Configuration.VALUECOLKEY):
                raise ConfigurationError("Text element %s should have at least %s key"%(elem,Configuration.VALUECOLKEY))
#            if not elem.has_key(Configuration.ERRORCOLKEY) and not elem.has_key(Configuration.ERRORTYPEKEY):
#                raise ConfigurationError("Text element %s should have at least %s or %s key"%(elem,Configuration.ERRORCOLKEY + Configuration.ERRORTYPEKEY))
#                raise ConfigurationError("Text element %s should have at least %s or %s key"%(elem,Configuration.ERRORCOLKEY,Configuration.ERRORTYPEKEY))
        _logger.debug("Configuration syntax for '%s' checked and passed"%Configuration.TEXTKEY) 

    def fillRefData(self,fileNameRef) : 
#        fileNameRef = self.text[Configuration.REFERENCEKEY]
        _logger.debug("START fillRefData %s RR"% fileNameRef)
        self.theNEventsRef = 0
        try:
            fin = open(fileNameRef)
        except IOError as e:
            sys.stderr.write("!!! No such file %s\n"%fileNameRef)
            sys.exit(1)
#            print "I/O error({0}): {1}".format(e.errno, e.strerror)
      # check file exists
        lines = fin.readlines()
        for line in lines:
            line = line.lstrip()
            _logger.debug("@@@ check line: %s "% line )
            words = SplitLine(line)
#--- check if it correspond to one line
            for dline in self.text[Configuration.LINESKEY] :
#                _logger.debug("line value %s "% dline[Configuration.VALUECOLKEY] ) 
                dwords =  dline[Configuration.WORDSKEY] 
#                _logger.debug("len WORDS %s "% len(dwords) )
                bLineOK = 1
                if type(dwords)!=type(dict()):
                    _logger.debug("WORD IS NOT DICT")
                for dwordk in dwords :
#                    for dwork in dwords:
                    if dwordk < 0 or dwordk >= len(words) :
                        bLineOK = 0
                        break
                    _logger.debug("WORDDATA CHK %s = %s"% (words[dwordk-1],dline[Configuration.WORDSKEY][dwordk]))
                    if words[dwordk-1] <> dline[Configuration.WORDSKEY][dwordk] : 
                        bLineOK = 0
                        break
                if bLineOK :
                    _logger.debug("REF FILE: LINE MATCHES CONFIGURATION: %s "% line)
                    if dline[Configuration.VALUECOLKEY] > len(words)  :
                        raise ConfigurationError("Line too short to get reference value , %s < %s "%(len(words),dline [Configuration.VALUECOLKEY]) )
                    dline['ValueRef'] = words[ dline[Configuration.VALUECOLKEY]-1 ].rstrip()
                    if dline[Configuration.ERRORTYPEKEY] == "ABS" : 
                        if dline[Configuration.ERRORCOLKEY] > len(words)  :
                            raise ConfigurationError("Line too short to get reference error , %s < %s "%(len(words),dline [Configuration.ERRORCOLKEY] ))
                        dline['ErrorRef'] = words[ dline[Configuration.ERRORCOLKEY]-1 ].rstrip()
                    elif dline[Configuration.ERRORTYPEKEY] == "REL" : 
                        if dline[Configuration.ERRORCOLKEY] > len(words)  :
                            raise ConfigurationError("Line too short to get reference error , %s < %s "%(len(words),dline [Configuration.ERRORCOLKEY] ))
                        dline['ErrorRef'] = float(words[ dline[Configuration.ERRORCOLKEY]-1 ])*float(dline['ValueRef'].rstrip())
                    elif dline[Configuration.ERRORTYPEKEY] == "REL100" : 
                        if dline[Configuration.ERRORCOLKEY] > len(words)  :
                            raise ConfigurationError("Line too short to get reference error , %s < %s "%(len(words),dline [Configuration.ERRORCOLKEY] ))
                        dline['ErrorRef'] = float(words[ dline[Configuration.ERRORCOLKEY]-1 ])*float(dline['ValueRef'].rstrip())/100.
                    elif dline[Configuration.ERRORTYPEKEY] == "RELFIX" : 
                        if dline[Configuration.ERRORCOLKEY] > len(words)  :
                            raise ConfigurationError("Line too short to get reference error , %s < %s "%(len(words),dline [Configuration.ERRORCOLKEY] ))
                        dline['ErrorRef'] = float(dline[Configuration.ERRORCOLKEY])*float(dline['ValueRef'].rstrip())
                    else : 
                        raise ConfigurationError("Error type is not valid: %s it should be 'ABS', 'REL', 'REL100' or 'RELFIX'"%dline[Configuration.ERRORTYPEKEY] )

#### Read text file and check if lines defined by configuration are found
    def readTextFile( self, aFileName):
        _logger.debug("START readTextFile %s"% aFileName)
        try:
            fin = open(aFileName)
        except IOError as e:
            # check file exists
            sys.stderr.write("!!! No such file %s\n"%aFileName)
            sys.exit(1)
        lines = fin.readlines()
        for line in lines:
            line = line.lstrip()
            _logger.debug("@@@ check line %s "% line )
            words = SplitLine(line)
            _logger.debug("checking len words %f "% len(words))
            for word1 in words :
                _logger.debug("checking words %s "% word1)
#--- check if it correspond to one line
            for dline in self.text[Configuration.LINESKEY] :
                _logger.debug("checking dline %s "% dline)
                dwords = dline[Configuration.WORDSKEY] 
            #                _logger.debug("len WORDS %s "% len(dwords) )
                bLineOK = 1
                if type(dwords)!=type(dict()):
                    _logger.debug("WORD IS NOT DICT")
                for dwordk in dwords :
                    _logger.debug("checking dword %s : %s "% (dwordk,dline[Configuration.WORDSKEY][dwordk]))
                    if dwordk < 0 or dwordk >= len(words) :
                        bLineOK = 0
                        break
                    _logger.debug("TWORDDATA CHK %s = %s"% (words[dwordk-1],dline[Configuration.WORDSKEY][dwordk]))
                    if words[dwordk-1] <> dline[Configuration.WORDSKEY][dwordk] : 
                        bLineOK = 0
                        break
                if bLineOK :
                    _logger.debug("TEXT FILE: LINE MATCHES CONFIGURATION: %s "% line)
                    if dline[Configuration.VALUECOLKEY] > len(words)  :
                        raise ConfigurationError("Line too short to get reference value , %s < %s "%(len(words),dline [Configuration.VALUECOLKEY]) )
                    dline['Value'] = words[ dline[Configuration.VALUECOLKEY]-1 ].rstrip()
                    if dline[Configuration.ERRORTYPEKEY] == "ABS" : 
                       if dline[Configuration.ERRORCOLKEY] > len(words)  :
                           raise ConfigurationError("Line too short to get reference error , %s < %s "%(len(words),dline [Configuration.ERRORCOLKEY] ))
                       dline['Error'] = words[ dline[Configuration.ERRORCOLKEY]-1 ].rstrip()
                    elif dline[Configuration.ERRORTYPEKEY] == "REL" : 
                        if dline[Configuration.ERRORCOLKEY] > len(words)  :
                            raise ConfigurationError("Line too short to get reference error , %s < %s "%(len(words),dline [Configuration.ERRORCOLKEY] ))
                        dline['Error'] = float(words[ dline[Configuration.ERRORCOLKEY]-1 ])*float(dline['ValueRef'].rstrip())
                    elif dline[Configuration.ERRORTYPEKEY] == "REL100" : 
                        if dline[Configuration.ERRORCOLKEY] > len(words)  :
                            raise ConfigurationError("Line too short to get reference error , %s < %s "%(len(words),dline [Configuration.ERRORCOLKEY] ))
                        dline['Error'] = float(words[ dline[Configuration.ERRORCOLKEY]-1 ])*float(dline['ValueRef'].rstrip())/100.
                    elif dline[Configuration.ERRORTYPEKEY] == "RELFIX" : 
                        if dline[Configuration.ERRORCOLKEY] > len(words)  :
                            raise ConfigurationError("Line too short to get reference error , %s < %s "%(len(words),dline [Configuration.ERRORCOLKEY] ))
                        dline['Error'] = float(dline[Configuration.ERRORCOLKEY])*float(dline['ValueRef'].rstrip())
                    else : 
                        raise ConfigurationError("Error type is not valid: %s it should be 'ABS', 'REL', 'REL100' or 'RELFIX'"%dline[Configuration.ERRORTYPEKEY] )
                    if dline['ErrorRef'] != 0 :
                        nsig = (float(dline['Value'])-float(dline['ValueRef']))/float(dline['ErrorRef'])
                    else :
                        nsig = 0
                    msg = self.getTextLineName(dline) + " VALUE= " + str(dline['Value']).rstrip() + " REF_VALUE= " + str(dline['ValueRef']).rstrip() + " REF_ERROR= " + str(dline['ErrorRef']).rstrip() + " : " + str(nsig)
                    _logger.info(" TEXT LINE FOUND %s"%msg)
                _logger.debug("ENDED checking dline %s "% dline)
            _logger.debug("ENDED checking line %s "% line)

        _logger.info("ENDED readTextFile()")
                
#t check line is not found twice

    def getTextLineName(self,dline):
        name = ""
        dwords = dline[Configuration.WORDSKEY] 
        for dwordk in dwords :
#            name = name + str(dwordk) + " : " + str(dline[Configuration.WORDSKEY][dwordk]) + " | " 
            name = name + str(dline[Configuration.WORDSKEY][dwordk]) + " "
        return name

    def getTextDefaultTest(self):
        """
        Returns default test
        """
        return self.text[Configuration.DEFAULTTESTKEY]

    def getTextDefaultThresholds(self):
        """
        Return default thresholds
        """
        return self.text[Configuration.DEFAULTTHRESHOLDSKEY]

    def getLines(self):
        """
        Return all histos configurations
        """
        return self.text[Configuration.LINESKEY]
                
    def parseAndCheckUnBinned(self):
        """
        Check configuration for UnBinned distributions
        """
        _logger.debug("Checking configuration syntax for 'UnBinned'")
        if not self.configuration.has_key(Configuration.UNBINNEDKEY):
            _logger.debug("No 'UnBinned' configuration, nothing to do")
            return
        self.unbinned=self.configuration[Configuration.UNBINNEDKEY]
        if type(self.unbinned)!=type(dict()):
            raise ConfigurationError("UnBinned block should be of type dict")
        #If not specified, add defaults placeholders
        if not self.unbinned.has_key(Configuration.DEFAULTTESTKEY):
            self.unbinned[Configuration.DEFAULTTESTKEY]=None
        if not self.unbinned.has_key(Configuration.DEFAULTREFKEY):
            self.unbinned[Configuration.DEFAULTREFKEY]=None
        if not self.unbinned.has_key(Configuration.DEFAULTTHRESHOLDSKEY):
            self.unbinned[Configuration.DEFAULTTHRESHOLDSKEY]=None
        else:
            if type(self.unbinned[Configuration.DEFAULTTHRESHOLDSKEY])!=type(list()) or \
                len(self.unbinned[Configuration.DEFAULTTHRESHOLDSKEY])!=2:
                raise ConfigurationError("Thresholds should be a list of size 2")
        if not self.unbinned.has_key(Configuration.DATASETKEY):
            raise ConfigurationError("UnBinned block should have at least a %s variable"%Configuration.DATASETKEY)
        if type(self.unbinned[Configuration.DATASETKEY])!=type(list()):
            raise ConfigurationError("%s element should be of type list"%Configuration.DATASETKEY)
        if len(self.unbinned[Configuration.DATASETKEY])==0:
            raise ConfigurationError("%s element should contain at least one dictionary"%Configuration.DATASETKEY)
        for elem in self.unbinned[Configuration.DATASETKEY]:
            if type(elem)!=type(dict()):
                raise ConfigurationError("%s element %s should be of type dictionary"%(Configuration.DATASETKEY,elem))
            if not elem.has_key(Configuration.NAMEKEY):
                raise ConfigurationError("%s element %s should have at least %s key"%(Configuration.DATASETKEY,elem,Configuration.NAMEKEY))
            if elem.has_key(Configuration.THRESHOLDSKEY):
                if type(elem[Configuration.THRESHOLDSKEY])!=type(list()) or \
                    len(elem[Configuration.THRESHOLDSKEY])!=2:
                    raise ConfigurationError("%s should be a list of size 2"%Configuration.THRESHOLDSKEY)
            if elem.has_key(Configuration.LOGXKEY):
                if type(elem[Configuration.LOGXKEY])!=type(True):
                    raise ConfigurationError("Key %s in element %s should be a boolean"%(Configuration.LOGXKEY,elem))
            else:
                elem[Configuration.LOGXKEY] = False
            if elem.has_key(Configuration.LOGYKEY):
                if type(elem[Configuration.LOGYKEY])!=type(True):
                    raise ConfigurationError("Key %s in element %s should be a boolean"%(Configuration.LOGYKEY,elem))
            else:
                elem[Configuration.LOGYKEY] = False
        _logger.debug("Configuration syntax for '%s' checked and passed"%Configuration.DATASETKEY)
            
    def parseAndCheckBinned(self):
        """
        Check configuration for Binned distributions
        """
        _logger.debug("Checking configuration syntax for 'Binned'")
        if not self.configuration.has_key(Configuration.BINNEDKEY):
            _logger.debug("No 'Binned' configuration, nothing to do")
            return
        self.binned=self.configuration[Configuration.BINNEDKEY]
        if type(self.binned)!=type(dict()):
            raise ConfigurationError("Binned block should be of type dict")
        #If not specified, add defaults placeholders
        if not self.binned.has_key(Configuration.DEFAULTTESTKEY):
            self.binned[Configuration.DEFAULTTESTKEY]=None
        if not self.binned.has_key(Configuration.DEFAULTREFKEY):
            self.binned[Configuration.DEFAULTREFKEY]=None
        if not self.binned.has_key(Configuration.DEFAULTTHRESHOLDSKEY):
            self.binned[Configuration.DEFAULTTHRESHOLDSKEY]=None
        else:
            if type(self.binned[Configuration.DEFAULTTHRESHOLDSKEY])!=type(list()) or \
                len(self.binned[Configuration.DEFAULTTHRESHOLDSKEY])!=2:
                raise ConfigurationError("Thresholds should be a list of size 2")
        if not self.binned.has_key(Configuration.HISTOSKEY):
            raise ConfigurationError("Binned block should have a %s variable"%Configuration.HISTOSKEY)
        if type(self.binned[Configuration.HISTOSKEY])!=type(list()):
            raise ConfigurationError("%s variable should be of type list"%Configuration.HISTOSKEY)
        if len(self.binned[Configuration.HISTOSKEY])==0:
            raise ConfigurationError("Histo variable should contain at least one dictionary")
        for elem in self.binned[Configuration.HISTOSKEY]:
            if type(elem)!=type(dict()):
                raise ConfigurationError("Histo element %s should be of type dictionary"%elem)
            if not elem.has_key(Configuration.NAMEKEY):
                raise ConfigurationError("Histo element %s should have at least %s key"%(elem,Configuration.NAMEKEY))
            if elem.has_key(Configuration.THRESHOLDSKEY):
                if type(elem[Configuration.THRESHOLDSKEY])!=type(list()) or \
                    len(elem[Configuration.THRESHOLDSKEY])!=2:
                    raise ConfigurationError("Thresholds should be a list of size 2")
            if elem.has_key(Configuration.LOGXKEY):
                if type(elem[Configuration.LOGXKEY])!=type(True):
                    raise ConfigurationError("Key %s in histo element %s should be a boolean"%(Configuration.LOGXKEY,elem))
            else:
                elem[Configuration.LOGXKEY] = False
            if elem.has_key(Configuration.LOGYKEY):
                if type(elem[Configuration.LOGYKEY])!=type(True):
                    raise ConfigurationError("Key %s in histo element %s should be a boolean"%(Configuration.LOGYKEY,elem))
            else:
                elem[Configuration.LOGYKEY] = False
        _logger.debug("Configuration syntax for '%s' checked and passed"%Configuration.BINNEDKEY) 

    def getConfigurationForHisto( self, name ):
        """
        Return configuration for name
        """
        import re
        for elem in self.binned[Configuration.HISTOSKEY]:
            #Histogram name can be regexp
            if re.match("^%s$"%elem[Configuration.NAMEKEY],name) or elem[Configuration.NAMEKEY] == name :
                return elem
        return None
    
    def getHistos(self):
        """
        Return all histos configurations
        """
        return self.binned[Configuration.HISTOSKEY]
                
    def getHistosNames(self):
        """
        Returns all histograms names
        """
        return [ hh[Configuration.NAMEKEY] for hh in self.getHistos() ]

    def getHistosDefaultTest(self):
        """
        Returns default test
        """
        return self.binned[Configuration.DEFAULTTESTKEY]

    def getHistosDefaultThrsholds(self):
        """
        Returns default thresholds
        """
        return self.binned[Configuration.DEFAULTTHRESHOLDSKEY]
    
    def getHistosDefaultReferenceFile(self):
        """
        Returns default reference file
        """
        return self.binned[Configuration.DEFAULTREFKEY]

    def getConfigurationForUnbinned(self,name):
        """
        Return configuration for name
        """
        import re
        for elem in self.unbinned[Configuration.DATASETKEY]:
            if re.match("^%s$"%elem[Configuration.NAMEKEY],name) or elem[Configuration.NAMEKEY] == name :
                return elem
        return None
    
    def getUnbinned(self):
        """
        Return all unbinned distributions configurations
        """
        return self.unbinned[Configuration.DATASETKEY]

    def getUnbinnedNames(self):
        """
        Returns all unbinned distribution names
        """
        return [ tb[Configuration.NAMEKEY] for tb in self.getUnbinned() ]

    def getUnbinnedDefaultTest(self):
        """
        Return default test
        """
        return self.unbinned[Configuration.DEFAULTTESTKEY]
    def getUnbinnedDefaultThresholds(self):
        """
        Return default thresholds
        """
        return self.unbinned[Configuration.DEFAULTTHRESHOLDSKEY]
        
    def getUnbinnedDefaultReferenceFile(self):
        """
        Return default reference file
        """
        return self.unbinned[Configuration.DEFAULTREFKEY]
            
    def __str__(self):
        msg = "Active configuration from file: %s"%self.filename
        if self.__dict__.has_key('binned'):
            msg+="\n For binned distributions:\n\t{\n"
            for k,v in self.binned.iteritems():
                msg+="\t%s : %s\n"%(k,v)
            msg+="\t}\n"
        if self.__dict__.has_key('unbinned'):
            msg+="\n For unbinned distributions:\n\t{\n"
            for k,v in self.unbinned.iteritems():
                msg+="\t%s : %s\n"%(k,v)
            msg+="\t}\n"
        msg+="\n"
        return msg



_openRootFiles = []
######################################################
def runROOT( aConfigurationFile , aFileName, doText = False , doHistos = True , doUnBinned = True , doPlots = None , defaultReferenceFile = None , useColorsForOutput = False):
    """
    Run full analysis for a ROOT file.
    Configuraiton is specified in aConfiguraitonFile, the input ROOT file
    is aROOTTfileName.
    """
    _logger.info("Preparing to run tests for run")
    _logger.info("Reading configuration from file: %s"%aConfigurationFile)
    _logger.info("Inputs are contained in file: %s"%aFileName)
    _logger.info("Report in file: %s"%doPlots)
    conf = Configuration(aConfigurationFile)
    _logger.debug("Configuration is: %s"%conf)
    tfilecontent = []
    #We need to reduce verbosity in ROOT...
    #See: http://root.cern.ch/phpBB3/viewtopic.php?t=10902&p=46976
    import ROOT
    ROOT.gErrorIgnoreLevel = 1001

    from sys import stdout,stderr
    from ROOTIO import makePage

    openpage = True
    errcode = 0

    #Text part...
    if doText:
        _logger.info("Processing text lines")
        conf.parseAndCheckText()
        _logger.debug("After parse ")
        _logger.debug("REF FILE : %s"%defaultReferenceFile)
        if defaultReferenceFile:
            _logger.debug("Overwriting default reference files with %s"%defaultReferenceFile)
            conf.text[Configuration.DEFAULTREFKEY]=defaultReferenceFile
            conf.text[Configuration.REFERENCEKEY]=defaultReferenceFile
        #Open ROOT file and get its content...
        refFile = conf.text[Configuration.REFERENCEKEY]
        _logger.debug("Before call reffile %s "%refFile)
        conf.fillRefData(refFile)
#        conf.fillRefData(conf.text[Configuration.REFERENCEKEY])
        _logger.debug("After call reffile %s"%conf.text[Configuration.REFERENCEKEY])
        conf.readTextFile( aFileName )
    _logger.debug("READTEXTFILE CALLED")

    if doHistos:
        _logger.info("Processing histograms")
        conf.parseAndCheckBinned()
    try:
        conf.binned
    except:
        #Disable because they do not exist in conf file
        doHistos = False
    if doUnBinned:
        _logger.debug("Starting configuration of unbinned distributions")
        conf.parseAndCheckUnBinned()
    try:
        conf.unbinned
    except:
        #Disable because they do not exists in conf file
        doUnBinned = False

    if not doHistos and not doUnBinned and not doText:
        raise ConfigurationError("No 'Binned', 'UnBinned' or 'Text' configurations found in conf file")
    if doHistos or doUnBinned:        
#        if defaultReferenceFile:
#            _logger.debug("Overwriting default reference files with %s"%defaultReferenceFile)
#            conf.binned[Configuration.DEFAULTREFKEY]=defaultReferenceFile
        #Open ROOT file and get its content...
        from ROOT import TFile
        _logger.debug("Reading file content...")
        tfile = TFile.Open( aFileName )
        import ROOTIO
        tfilecontent += ROOTIO.readDirectory( tfile )
        _logger.debug("Input file read. It contains %d objects"%len(tfilecontent))

    #This contains Algorithms objects
    theAlgorithms = []
    if doText:
        #Now loop on lines, store Algorithms to be executed
        for dline in conf.text[Configuration.LINESKEY] :
# only if dline was found in reference file
             if dline.has_key(Configuration.VALUEKEY):
                 _logger.debug("Configuration: %s"%dline)
            #If test is not specified use default
                 if not dline.has_key(Configuration.TESTNAMEKEY):
                     _logger.debug("No test specified, using default")
                     reftest=conf.getTextDefaultTest()
                     if reftest == None:
                         _logger.debug("No default specified, cannot continue")
                         raise ConfigurationError("No test specified for: %s"%dline)
                     dline[Configuration.TESTNAMEKEY]=reftest
            #Create the ouput object to store result
            #If threholds are specified, use them
                 _logger.debug("Creating Result object with name: %s"%conf.getTextLineName(dline))
            #If thresholds not specified use default
                 if not dline.has_key(Configuration.THRESHOLDSKEY):
                     _logger.debug("No thresholds specified, using default")
                     refthre=conf.getTextDefaultThresholds()
                     if refthre == None:
                         _logger.debug("No default specified, cannot continue")
                         raise Configuration("No thresholds specified for: %s"%hin)
                     dline[Configuration.THRESHOLDSKEY]=refthre
                 theResult = Output( name = conf.getTextLineName(dline) ,
                                     failedThreshold = dline[Configuration.THRESHOLDSKEY][0] ,
                                     passedThreshold = dline[Configuration.THRESHOLDSKEY][1])
            #Now create Test object, it needs one line as input:
                 from Tests import getTestByName
                 _logger.debug("Creating test with name: %s"%dline[Configuration.TESTNAMEKEY])
                 testClass = getTestByName( dline[Configuration.TESTNAMEKEY] )

                 theTest = testClass( dline )
            #Finally we can build the Algorithm object: a test with an output
                 theAlgo = Algorithm( theTest , theResult )
                 _logger.debug("Algorithm created %s"%theAlgo)
                 theAlgorithms.append( theAlgo )
                 #theAlgo.check()
            #End of loops on input histograms

    if doHistos:
        if defaultReferenceFile:
            _logger.debug("Overwriting default reference files with %s"%defaultReferenceFile)
            conf.binned[Configuration.DEFAULTREFKEY]=defaultReferenceFile
        #Now select only histograms really needed...
        selectedHistos = []
        import re
        _logger.debug("Matching input file content with 'Histos' configuraitons defined in configuration file")
        for selection in conf.getHistosNames():
            _logger.debug("Searching matches for: %s"%selection)
            mm=re.compile( "^%s$"%selection )
            for el in tfilecontent:
                _logger.debug('Checking match for: %s against selection: %s'%(el,selection))
                if mm.match( el ) or el == selection:
                    _logger.debug("Match found %s"%el)
                    selectedHistos.append( el )
        #Build IO.Histogram objects for all selected histograms
        _logger.debug("Histograms matching selections in configuration file: %d"%len(selectedHistos))
        _logger.debug("Creating IO.Input objects for selected input")
        histos = ROOTIO.buildHistogramInputs( tfile , selectedHistos )
        #Now loop on histograms, store Algorithms to be executed
        for hin in histos:
            _logger.info("Getting configuration for: %s"%hin.name)
            #Get configuration for specific histogram
            cc = conf.getConfigurationForHisto( hin.name )
            _logger.debug("Configuration: %s"%cc)
            #If reference is not specified use default
            if not cc.has_key(Configuration.REFERENCEKEY):
                _logger.debug("No reference file specified, using default")
                reffile=conf.getHistosDefaultReferenceFile()
                if reffile == None:
                    _logger.debug("No default specified, cannot continue")
                    raise ConfigurationError("No reference specified for: %s"%hin)
                cc[Configuration.REFERENCEKEY]=reffile
            #If test is not specified use default
            if not cc.has_key(Configuration.TESTNAMEKEY):
                _logger.debug("No test specified, using default")
                reftest=conf.getHistosDefaultTest()
                if reftest == None:
                    _logger.debug("No default specified, cannot continue")
                    raise ConfigurationError("No test specified for: %s"%hin)
                cc[Configuration.TESTNAMEKEY]=reftest
            #If thresholds not specified use default
            if not cc.has_key(Configuration.THRESHOLDSKEY):
                _logger.debug("No thresholds specified, using default")
                refthre=conf.getHistosDefaultThrsholds()
                if refthre == None:
                    _logger.debug("No default specified, cannot continue")
                    raise Configuration("No thresholds specified for: %s"%hin)
                cc[Configuration.THRESHOLDSKEY]=refthre
            _logger.debug("Final configuration for object: %s"%cc)
            #Create the ouput object to store result
            #If threholds are specified, use them
            #for algo in theAlgorithms:
            #    _logger.info("loop algo pre1.. %s", algo.test.dataset1) # GDEB
            #    _logger.info("loop algo pre1.. %s", algo.test.dataset2) # GDEB
            _logger.debug("Creating Result object with name: %s"%hin.name)
            theResult = Output( name = hin.name ,
                                failedThreshold = cc[Configuration.THRESHOLDSKEY][0] ,
                                passedThreshold = cc[Configuration.THRESHOLDSKEY][1] ,
                                logx = cc[Configuration.LOGXKEY],
                                logy = cc[Configuration.LOGYKEY])
            #Now create Test object, it needs two histograms as input:
            # The actual histogram to be checked (hold by Input object)
            # and a reference histogram in the reference TFile
            from Tests import getTestByName
            _logger.debug("Creating test with name: %s"%cc[Configuration.TESTNAMEKEY])
            testClass = getTestByName( cc[Configuration.TESTNAMEKEY] )
            hobj = hin.getObject()
            #for algo in theAlgorithms:
            #    _logger.info("loop algo pre2.. %s", algo.test.dataset1) # GDEB
            #    _logger.info("loop algo pre2.. %s", algo.test.dataset2)  # GDEB
           #Get reference: same name as input
            _logger.debug("Reading reference from reference file")
            fref = TFile.Open( cc[Configuration.REFERENCEKEY] )
            _openRootFiles.append(fref) #Force ROOT files to remain open, otherwise histos may be deleted
            #for algo in theAlgorithms:
            #    _logger.info("loop algo pre3.. %s", algo.test.dataset1) # GDEB
            #    _logger.info("loop algo pre3.. %s", algo.test.dataset2) # GDEB
            _logger.debug("Reference file is: %s (%s)"%(fref.GetName(),fref))
            href = fref.Get( hin.name )
            _logger.info("Reference object: %s"%href)
            theTest = testClass( hobj, href )
            #Finally we can build the Algorithm object: a test with an output
            theAlgo = Algorithm( theTest , theResult )
            _logger.debug("Algorithm created %s"%theAlgo)
            theAlgorithms.append( theAlgo )
    if doUnBinned:
        if defaultReferenceFile:
            _logger.debug("Overwriting default reference files with %s"%defaultReferenceFile)
            conf.unbinned[Configuration.DEFAULTREFKEY]=defaultReferenceFile
        selectedUnbinned = []
        import re
        for selection in conf.getUnbinnedNames():
            #Name has format TreeName:BranchName
            _logger.debug("Searching matches for: %s"%selection)
            treename = selection[:selection.find(":")]
            branchname = selection[selection.find(":")+1:]
            tm = re.compile("^%s$"%treename)
            for aTreeNameCand in tfilecontent:
                _logger.debug("Checking match for: %s against tree name: %s"%(aTreeNameCand,treename))
                if tm.match(aTreeNameCand):
                    _logger.debug("Match found, checking if element is TTree containing branch matching %s"%branchname)
                    foundbranchname = ROOTIO.checkTreeHasBranch( tfile , aTreeNameCand , branchname ) 
                    if foundbranchname != None:
                        _logger.debug("Branch named %s matches selection: %s"%(foundbranchname,branchname))
                        theUnbinnedConfiguration = conf.getConfigurationForUnbinned( selection )
                        selectedUnbinned.append( (aTreeNameCand,foundbranchname,theUnbinnedConfiguration) )
        _logger.debug("Found %d unbinned distributions to configure"%len(selectedUnbinned))
        unbinnedinputs = ROOTIO.buildUnbinnedInputs ( tfile , selectedUnbinned )
        #Reference Files: keep reference files open
        frefs = {}
        for unb in unbinnedinputs:
            _logger.info("Getting configuration for: %s"%unb.name)
            cc=conf.getConfigurationForUnbinned( unb.name )
            _logger.debug("Configuration: %s"%cc)
            #It reference is not specified use default
            if not cc.has_key(Configuration.REFERENCEKEY):
                _logger.debug("No reference file specified, using default")
                reffile=conf.getUnbinnedDefaultReferenceFile()
                if reffile == None:
                    _logger.debug("No default specified, cannot continue")
                    raise ConfigurationError("No reference specified for: %s"%unb)
                cc[Configuration.REFERENCEKEY]=reffile
            #If test is not specified use default
            if not cc.has_key(Configuration.TESTNAMEKEY):
                    _logger.debug("No test specified, using default")
                    reftest=conf.getUnbinnedDefaultTest()
                    if reftest == None:
                        _logger.debug("No default specified, cannot continue")
                        raise ConfigurationError("No test specified for: %s"%unb)
                    cc[Configuration.TESTNAMEKEY]=reftest
            #If thresholds not specified use default
            if not cc.has_key(Configuration.THRESHOLDSKEY):
                    _logger.debug("No thresholds specified, using default")
                    refthre=conf.getUnbinnedDefaultThresholds()
                    if refthre == None:
                        _logger.debug("No default specified, cannot continue")
                        raise Configuration("No thresholds specified for: %s"%unb)
                    cc[Configuration.THRESHOLDSKEY]=refthre
            _logger.debug("Final configuration for object: %s"%cc)
            #Create the ouput object to store result
            #If threholds are specified, use them
            _logger.debug("Creating Result object with name: %s"%unb.name)
            theResult = Output( name = unb.name ,
                               failedThreshold = cc[Configuration.THRESHOLDSKEY][0] ,
                               passedThreshold = cc[Configuration.THRESHOLDSKEY][1] ,
                               logx = cc[Configuration.LOGXKEY],
                               logy = cc[Configuration.LOGYKEY])
            #Now create Test object, it needs two histograms as input:
            # The actual histogram to be checked (hold by Input object)
            # and a reference histogram in the reference TFile
            from Tests import getTestByName
            _logger.debug("Creating test with name: %s"%cc[Configuration.TESTNAMEKEY])
            testClass = getTestByName( cc[Configuration.TESTNAMEKEY] )
            #obj = unb.getObject()
            #Get reference: same name as input
            _logger.debug("Reading reference from reference file")
            #Check if reference file is already open
            if frefs.has_key( cc[Configuration.REFERENCEKEY] ):
                fref = frefs[ cc[Configuration.REFERENCEKEY] ]
            else:
                fref = TFile.Open( cc[Configuration.REFERENCEKEY] )
                frefs[ cc[Configuration.REFERENCEKEY] ] = fref
            _logger.debug("Reference file is: %s (%s)"%(fref.GetName(),fref))
            treename = unb.name[:unb.name.find(":")]
            branchname = unb.name[unb.name.find(":")+1:]
            ref = ROOTIO.checkTreeHasBranch( fref , treename , branchname )
            if ref == None:
                raise ConfigurationError("Reference branch: %s in tree: %s in reference file: %s not found"%(branchname,treename,fref.GetName()))
            refobj = ROOTIO.buildUnbinnedInputs( fref , [(treename,ref,cc)])[0]
            _logger.debug("Reference object: %s"%refobj)
            #print refobj
            #print unb
            theTest = testClass( unb, refobj )
            
            #Finally we can build the Algorithm object: a test with an output
            theAlgo = Algorithm( theTest , theResult )
            _logger.debug("Algorithm created %s"%theAlgo)
            theAlgorithms.append( theAlgo )
            #theAlgo.check()
    _logger.info("Configuration done, a total of %d Algorithms have been created"%len(theAlgorithms))
    _logger.info("Executing ...")
    [ algo.check() for algo in theAlgorithms ]
    _logger.info("Printing results...")
    print "="*80
    from sys import stdout,stderr
    from ROOTIO import makePage
    openpage = True
    errcode = 0
    for algo in theAlgorithms:
        stdout.write(" ")
        errcode += algo.output.pprint( stdout ,colors= useColorsForOutput )
        stdout.write(" (Test: %s)"%(algo.test.__class__.__name__))
        stdout.write(" (pval= %s)"%algo.output.value)
        stdout.write("\n")
        if doPlots != None:
            if openpage:
                makePage( algo , doPlots , "(")
                openpage = False
            else:
                makePage( algo , doPlots )
    print "="*80
    if doPlots != None:
        from ROOT import TCanvas,gROOT,TText,kRed,kBlue
        gROOT.SetBatch(True)
        c=TCanvas()
        t1=TText(0.05,0.7,"Reference: "+repr(defaultReferenceFile))
        t1.SetTextColor(kRed)
        t1.SetTextSize(0.02)
        t1.Draw()
        t2=TText(0.05,0.6,"Input: "+aFileName)
        t2.SetTextSize(0.02)
        t2.SetTextColor(kBlue)
        t2.Draw()
        import time
        t3=TText(0.05,0.5,time.strftime("Run at: %F, %T UTC", time.gmtime()))
        t3.SetTextSize(0.02)
        t3.Draw()
        c.Print("%s)"%doPlots)
    _logger.info("End")
    return errcode         

def testme(files=None):
    """
    Test function
    """
    import Tests
    from ROOT import TH1F,TFile
    if files != None:
        in1 = TFile( files[0] )
        in2 = TFile( files[1] )
        hname = "Spectra/hProtonSpectrum"
        h1=in1.Get( hname )
        h2=in2.Get( hname )
        print h1,h2
    else:
        h1 = TH1F("h1","h",100,-10,10)
        h2 = TH1F("h2","h",100,-10,10)
        h1.FillRandom("gaus")
        h2.FillRandom("gaus")
    from ROOT import TCanvas
    global c
    c=TCanvas()
    c.Divide(1,2)
    c.cd(1)
    h1.DrawCopy()
    h2.SetLineColor(2)
    h2.DrawCopy("same")
    from Utils import DataType
    #aTest = Tests.KolmogorovSmirnovTest( h1 , h2 , DataType.BINNED1D)
    aTest = Tests.Binned1DChi2Test(h1,h2)
    #print aTest.pval(),aTest.stat()
    aResult = Output("A-Test")
    anAlgo = Algorithm( aTest , aResult )
    c.cd(2)
    anAlgo.test.residuals.Draw()
    anAlgo.test.residuals.Draw()
    print anAlgo.check()
    print aResult
    return h1,h2,anAlgo.test.residuals
