import json, os;

try: # mDebugOutput use is Optional
  from mDebugOutput import ShowDebugOutput, fShowDebugOutput;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mDebugOutput'":
    raise;
  ShowDebugOutput = lambda fx: fx; # NOP
  fShowDebugOutput = lambda x, s0 = None: x; # NOP

from mFileSystemItem import cFileSystemItem;
import mHTTPProtocol;
try:
  import mHTTPServer as m0HTTPServer;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mHTTPServer'":
    raise;
  m0HTTPServer = None;

from mNotProvided import *;

from .cTreeNode import cTreeNode;

goIndexHTMLFile = cFileSystemItem(__file__).o0Parent.foGetChild("index.html").foMustBeFile();
gsbJSONMediaType = mHTTPProtocol.fsb0GetMediaTypeForExtension("json");
assert gsbJSONMediaType, \
    "Could not get media type for JSON data";
gsbTextMediaType = mHTTPProtocol.fsb0GetMediaTypeForExtension("txt");
assert gsbTextMediaType, \
    "Could not get media type for TEXT data";

def foCreateResponseForRequest(oRequest, uStatusCode, sbMediaType, sbBody, sb0Charset = None):
  return oRequest.foCreateResponse(
    uzStatusCode = uStatusCode,
    sb0MediaType = sbMediaType,
    sb0Body = sbBody,
    sb0Charset = sb0Charset,
    bAutomaticallyAddContentLengthHeader = True,
  );
def foCreateResponseForRequestAndFile(oRequest, oFile):
  # Pick a media type based on the extension or use the default if there
  # is no known media type for this extension.
  return oRequest.foCreateResponse(
    uzStatusCode = 200,
    sb0MediaType = mHTTPProtocol.fsb0GetMediaTypeForExtension(oFile.s0Extension) or b"application/octet-stream",
    sb0Body = oFile.fsbRead(),
    bAutomaticallyAddContentLengthHeader = True,
  );

class cTreeServer(cTreeNode):
  cTreeNode = cTreeNode;
  @ShowDebugOutput
  def __init__(oSelf, sTitle, bOffline = False, **dxHTTPServerArguments):
    fAssertType("sTitle", sTitle, str);
    cTreeNode.__init__(oSelf, "cTreeServer root node");
    if bOffline:
      oSelf.__o0HTTPServer = None;
    else:
      assert m0HTTPServer is not None, \
          "`cTreeServer` depends on `mHTTPServer` unless you call it with `bOffline = True`";
      oSelf.__o0HTTPServer = m0HTTPServer.cHTTPServer(oSelf.__ftxRequestHandler, **dxHTTPServerArguments);
    oSelf.sTitle = sTitle;
    oSelf.__bStatic = False;
    oSelf.doFile_by_sRelativeURL = {};
  
  @property
  def sbHostname(oSelf):
    assert oSelf.__o0HTTPServer is not None, \
        "`sbHostname` is not available in offline mode!";
    return oSelf.__o0HTTPServer.sbHostname;
  @property
  def uPortNumber(oSelf):
    assert oSelf.__o0HTTPServer is not None, \
        "`uPortNumber` is not available in offline mode!";
    return oSelf.__o0HTTPServer.uPortNumber;
  @property
  def ozSSLContext(oSelf):
    assert oSelf.__o0HTTPServer is not None, \
        "`ozSSLContext` is not available in offline mode!";
    return oSelf.__o0HTTPServer.ozSSLContext;
  @property
  def bSecure(oSelf):
    assert oSelf.__o0HTTPServer is not None, \
        "`bSecure` is not available in offline mode!";
    return oSelf.__o0HTTPServer.bSecure;
  @property
  def asbIPAddresses(oSelf):
    assert oSelf.__o0HTTPServer is not None, \
        "`sbIPAddress` is not available in offline mode!";
    return oSelf.__o0HTTPServer.asbIPAddresses;
  @property
  def bTerminated(oSelf):
    return not oSelf.__oTerminatedLock.bLocked;
  @property
  def oURL(oSelf):
    assert oSelf.__o0HTTPServer is not None, \
        "`oURL` is not available in offline mode!";
    return oSelf.__o0HTTPServer.oURL;
  
  @ShowDebugOutput
  def fMakeStatic(oSelf):
    oSelf.__bStatic = True;
  
  @ShowDebugOutput
  def fWait(oSelf):
    assert oSelf.__o0HTTPServer is not None, \
        "`fWait()` is not available in offline mode!";
    oSelf.__o0HTTPServer.fWait();
  
  @ShowDebugOutput
  def fStop(oSelf):
    assert oSelf.__o0HTTPServer is not None, \
        "`fStop()` is not available in offline mode!";
    oSelf.__o0HTTPServer.fStop();
  
  @ShowDebugOutput
  def fTerminate(oSelf):
    assert oSelf.__o0HTTPServer is not None, \
        "`fTerminate()` is not available in offline mode!";
    oSelf.__o0HTTPServer.fTerminate();
  
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
    oRequestURL = oHTTPServer.foGetURLForRequest(oRequest);
    sPath = oRequestURL.sURLDecodedPath;
#    print ("oRequest.sbURL: %s" % repr(oRequest.sbURL));
#    print ("oRequestURL: %s" % str(oRequestURL));
#    print ("oRequest.sURLDecodedPath: %s" % repr(oRequestURL.sURLDecodedPath));
    return (
      oSelf.__foCreateResponseForRequestAndPath(oRequest, sPath),
      True, # Allways stay connected to client.
    );
  
  @ShowDebugOutput
  def __foCreateResponseForRequestAndPath(oSelf, oRequest, sPath):
    print("handling request for %s" % repr(sPath));
    # Filter out invalid methods
    if oRequest.sbMethod.upper() != b"GET":
      fShowDebugOutput("Method %s is not allows" % repr(oRequest.sbMethod));
      return foCreateResponseForRequest(oRequest, 405, gsbTextMediaType, b"Method %s not allowed" % oRequest.sbMethod);
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
      return foCreateResponseForRequest(oRequest, 200, gsbJSONMediaType, bytes(sBody, "utf-8", "strict"), b"utf-8");
    if sPath == "/stop":
      fShowDebugOutput("GET %s => stopping..." % (sPath,));
      oSelf.fStop();
      return foCreateResponseForRequest(oRequest, 200, gsbTextMediaType, b"Stopping");
    
    # Path not found
    fShowDebugOutput("GET %s => not found!" % (sPath,));
    return foCreateResponseForRequest(oRequest, 404, gsbTextMediaType, b"URL %s not found" % oRequest.sbURL);
