import json, os;

try: # mDebugOutput use is Optional
  from mDebugOutput import *;
except: # Do nothing if not available.
  ShowDebugOutput = lambda fxFunction: fxFunction;
  fShowDebugOutput = lambda sMessage: None;
  fEnableDebugOutputForModule = lambda mModule: None;
  fEnableDebugOutputForClass = lambda cClass: None;
  fEnableAllDebugOutput = lambda: None;
  cCallStack = fTerminateWithException = fTerminateWithConsoleOutput = None;

from cTreeNode import cTreeNode;
from cFileSystemItem import cFileSystemItem;
import mHTTP;

goIndexHTMLFile = cFileSystemItem(__file__).oParent.foGetChild("index.html", bMustBeFile = True);
gsJSONMediaType = mHTTP.fs0GetMediaTypeForExtension("json");
assert gsJSONMediaType, \
    "Could not get media type for JSON data";
gsTextMediaType = mHTTP.fs0GetMediaTypeForExtension("txt");
assert gsTextMediaType, \
    "Could not get media type for TEXT data";

def foCreateResponseForRequest(oRequest, uStatusCode, sMediaType, sBody):
  return oRequest.foCreateReponse(
    uzStatusCode = uStatusCode,
    s0MediaType = sMediaType,
    s0Body = sBody,
    bAutomaticallyAddContentLengthHeader = True,
  );
def foCreateResponseForRequestAndFile(oRequest, oFile):
  # Pick a media type based on the extension or use the default if there
  # is no known media type for this extension.
  return oRequest.foCreateReponse(
    uzStatusCode = 200,
    s0MediaType = mHTTP.fs0GetMediaTypeForExtension(oFile.sExtension) or "application/octet-stream",
    s0Body = oFile.fsRead(),
    bAutomaticallyAddContentLengthHeader = True,
  );

class cTreeServer(cTreeNode):
  cTreeNode = cTreeNode;
  @ShowDebugOutput
  def __init__(oSelf, sTitle, bOffline = False, **dxHTTPServerArguments):
    cTreeNode.__init__(oSelf, "cTreeServer root node");
    
    oSelf.__oHTTPServer = None if bOffline else mHTTP.cHTTPServer(oSelf.__ftxRequestHandler, **dxHTTPServerArguments);
    oSelf.sTitle = sTitle;
    oSelf.__bStatic = False;
    oSelf.doFile_by_sRelativeURL = {};
  
  @property
  def sHostname(oSelf):
    return oSelf.__oHTTPServer.sHostname;
  @property
  def uPort(oSelf):
    return oSelf.__oHTTPServer.uPort;
  @property
  def ozSSLContext(oSelf):
    return oSelf.__oHTTPServer.ozSSLContext;
  @property
  def bSecure(oSelf):
    return oSelf.__oHTTPServer.bSecure;
  @property
  def sIPAddress(oSelf):
    return oSelf.__oHTTPServer.sIPAddress;
  @property
  def bTerminated(oSelf):
    return not oSelf.__oTerminatedLock.bLocked;
  @property
  def oURL(oSelf):
    return oSelf.__oHTTPServer.oURL;
  
  @ShowDebugOutput
  def fMakeStatic(oSelf):
    oSelf.__bStatic = True;
  
  @ShowDebugOutput
  def fWait(oSelf):
    oSelf.__oHTTPServer.fWait();
  
  @ShowDebugOutput
  def fStop(oSelf):
    oSelf.__oHTTPServer.fStop();
  
  @ShowDebugOutput
  def fTerminate(oSelf):
    oSelf.__oHTTPServer.fTerminate();
  
  @ShowDebugOutput
  def fdxGetOfflineContent(oSelf, fProgressCallback = None):
    dxOfflineContent = {
      "index.html": goIndexHTMLFile,
      "dxTreeData.json": oSelf.fsGetTreeDataJSON(),
    };
    for (sRelativeURL, oFile) in oSelf.doFile_by_sRelativeURL.items():
      assert sRelativeURL[0] == "/", \
          "Absolute URL %s provide in doFile_by_sRelativeURL" % sRelativeURL;
      # Strip the leading "/" and replace all slashes with os path separators.
      sRelativePath = sRelativeURL[1:].replace("/", os.sep);
      dxOfflineContent[sRelativePath] = oFile;
    aoTreeNodes = [oSelf] + oSelf.faoGetDescendantsWithCallback(fProgressCallback);
    for oTreeNode in aoTreeNodes:
      if oTreeNode.oIconFile:
        sRelativePath = os.sep.join(["icons", oTreeNode.sNamespace, oTreeNode.oIconFile.sName]);
        if sRelativePath not in dxOfflineContent:
          dxOfflineContent[sRelativePath] = oTreeNode.oIconFile;
    return dxOfflineContent;
  
  def fsGetTreeDataJSON(oSelf):
    return json.dumps({
      "sTitle": oSelf.sTitle,
      "adxTreeNodes": [
        oTreeNode.fdxGetJSON()
        for oTreeNode in oSelf.aoChildren
      ],
      "nNextRefreshTimeoutInSeconds": None if oSelf.__bStatic else 1,
    });
  
  @ShowDebugOutput
  def __ftxRequestHandler(oSelf, oHTTPServer, oConnectionFromClient, oRequest):
    # Parse the URL in the request and extract the URL-decoded "path" component.
    sPath = oHTTPServer.foGetURLForRequest(oRequest).sURLDecodedPath;
    return (
      oSelf.__foCreateResponseForRequestAndPath(oRequest, sPath),
      True, # Allways stay connected to client.
    );
  
  @ShowDebugOutput
  def __foCreateResponseForRequestAndPath(oSelf, oRequest, sPath):
    # Filter out invalid methods
    if oRequest.sMethod.upper() != "GET":
      fShowDebugOutput("Method %s is not allows" % oRequest.sMethod);
      return (
        foCreateResponseForRequest(oRequest, 405, gsTextMediaType, "Method %s not allowed" % json.dumps(oRequest.sMethod)),
        True
      );
    # handle index HTML
    if sPath == "/":
      fShowDebugOutput("GET %s => index file %s" % (sPath, goIndexHTMLFile));
      return foCreateResponseForRequestAndFile(oRequest, goIndexHTMLFile);
    # handle icons
    if sPath.startswith("/icons/") and "/" in sPath[7:]:
      sNamespace, sIconFileName = sPath[7:].split("/", 1);
      for oDescendant in oSelf.aoDescendants:
        if oDescendant.sNamespace == sNamespace and oDescendant.oIconFile and oDescendant.oIconFile.sName == sIconFileName:
          fShowDebugOutput("GET %s => icon file %s" % (sPath, oDescendant.oIconFile));
          return foCreateResponseForRequestAndFile(oRequest, oDescendant.oIconFile);
      fShowDebugOutput("GET %s => icons namespace %s does not have a file %s" % (sPath, repr(sNamespace), repr(sIconFileName)));
    oFile = oSelf.doFile_by_sRelativeURL.get(sPath);
    if oFile:
      fShowDebugOutput("GET %s => file %s" % (sPath, oFile));
      return foCreateResponseForRequestAndFile(oRequest, oFile);
    # handle tree data JSON
    if sPath == "/dxTreeData.json":
      fShowDebugOutput("GET %s => tree data" % (sPath,));
      sBody = oSelf.fsGetTreeDataJSON();
      oSelf.fDiscardUserState();
      return foCreateResponseForRequest(oRequest, 200, gsJSONMediaType, sBody);
    if sPath == "/stop":
      fShowDebugOutput("GET %s => stopping..." % (sPath,));
      oSelf.fStop();
      return foCreateResponseForRequest(oRequest, 200, gsTextMediaType, "Stopping");
    
    # Path not found
    fShowDebugOutput("GET %s => not found!" % (sPath,));
    return foCreateResponseForRequest(oRequest, 404, gsTextMediaType, "URL %s not found" % json.dumps(oRequest.sURL));
