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
gsJSONMediaType = mHTTP.fsGetMediaTypeForExtension("json");
gsTextMediaType = mHTTP.fsGetMediaTypeForExtension("txt");

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
  def fdxGetOfflineContent(oSelf):
    dxOfflineContent = {
      "index.html": goIndexHTMLFile,
      "dxTreeData.json": oSelf.fsGetTreeDataJSON(),
    };
    for (sRelativeURL, oFile) in oSelf.doFile_by_sRelativeURL.items():
      assert sRelativeURL[0] != "/", \
          "Absolute URL %s provide in doFile_by_sRelativeURL" % sRelativeURL;
      # Strip the leading "/" and replace all slashes with os path separators.
      sRelativePath = sRelativeURL.replace("/", os.sep);
      dxOfflineContent[sRelativePath] = oFile;
    aoTreeNodes = [oSelf] + oSelf.aoDescendants;
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
    def ftxCreateResponse(uStatusCode, sMediaType, sBody):
      oResponse = oRequest.foCreateReponse(
        uzStatusCode = uStatusCode,
        szMediaType = sMediaType,
        szBody = sBody,
      );
      return (oResponse, True);
    def ftxCreateResponseForFile(oFile):
      return ftxCreateResponse(200, mHTTP.fsGetMediaTypeForExtension(oFile.sExtension), oFile.fsRead());

    # Filter out invalid methods
    if oRequest.sMethod.upper() != "GET":
      return ftxCreateResponse(405, gsTextMediaType, "Method %s not allowed" % json.dumps(oRequest.sMethod));
    sPath = oHTTPServer.foGetURLForRequest(oRequest).sURLDecodedPath;
    # handle index HTML
    if sPath == "/":
      return ftxCreateResponseForFile(goIndexHTMLFile);
    # handle icons
    if sPath.startswith("/icons/") and "/" in sPath[7:]:
      sNamespace, sIconFileName = sPath[7:].split("/", 1);
      for oDescendant in oSelf.aoDescendants:
        if oDescendant.sNamespace == sNamespace and oDescendant.oIconFile and oDescendant.oIconFile.sName == sIconFileName:
          return ftxCreateResponseForFile(oDescendant.oIconFile);
    if sPath in oSelf.doFile_by_sRelativeURL:
      return ftxCreateResponseForFile(oSelf.doFile_by_sRelativeURL[sPath]);
    # handle tree data JSON
    if sPath == "/dxTreeData.json":
      sBody = oSelf.fsGetTreeDataJSON();
      oSelf.fDiscardUserState();
      return ftxCreateResponse(200, gsJSONMediaType, sBody);
    if sPath == "/stop":
      oSelf.fStop();
      return ftxCreateResponse(200, gsTextMediaType, "Stopping");
    
    # Path not found
    return ftxCreateResponse(404, gsTextMediaType, "URL %s not found" % json.dumps(oRequest.sURL));
