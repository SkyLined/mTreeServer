import json, os;
from mHTTP import cHTTPServer, cURL, fsGetMediaTypeForExtension;
from cTreeNode import cTreeNode;
from cFileSystemItem import cFileSystemItem;

goIndexHTMLFile = cFileSystemItem(__file__).oParent.foGetChild("index.html", bMustBeFile = True);
gsJSONMediaType = fsGetMediaTypeForExtension("json");
gsTextMediaType = fsGetMediaTypeForExtension("txt");

def gfoCreateResponseForRequestAndFile(oRequest, oFile):
  assert oFile.fbIsFile(), \
      "%s is not a file!" % oFile.sPath;
  return oRequest.foCreateReponse(
    uStatusCode = 200,
    sMediaType = fsGetMediaTypeForExtension(oFile.sExtension),
    sBody = oFile.fsRead(),
  );

class cTreeServer(cTreeNode):
  cTreeNode = cTreeNode;
  def __init__(oSelf, sTitle, **dxHTTPServerArguments):
    cTreeNode.__init__(oSelf, "cTreeServer root node");
    
    oSelf.oHTTPServer = cHTTPServer(**dxHTTPServerArguments);
    oSelf.sURL = oSelf.oHTTPServer.sURL;
    oSelf.sTitle = sTitle;
    oSelf.__bStatic = False;
    oSelf.doFile_by_sRelativeURL = {};
  
  def fMakeStatic(oSelf):
    oSelf.__bStatic = True;
  
  def fStart(oSelf):
    oSelf.oHTTPServer.fStart(oSelf.__fRequestHandler);

  def fWait(oSelf):
    oSelf.oHTTPServer.fWait();
  
  def fStop(oSelf):
    oSelf.oHTTPServer.fStop();
  
  def fTerminate(oSelf):
    oSelf.oHTTPServer.fTerminate();
  
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
  def __fRequestHandler(oSelf, oHTTPServer, oConnectionFromClient, oRequest):
    # Filter out invalid methods
    if oRequest.sMethod.upper() != "GET":
      return oRequest.foCreateReponse(
        uStatusCode = 405,
        sMediaType = gsTextMediaType,
        sBody = "Method %s not allowed" % json.dumps(oRequest.sMethod),
      );
    
    sPath = oHTTPServer.foGetRequestURL(oRequest).sURLDecodedPath;
    # handle index HTML
    if sPath == "/":
      return gfoCreateResponseForRequestAndFile(oRequest, goIndexHTMLFile);
    # handle icons
    if sPath.startswith("/icons/") and "/" in sPath[7:]:
      sNamespace, sIconFileName = sPath[7:].split("/", 1);
      for oDescendant in oSelf.aoDescendants:
        if oDescendant.sNamespace == sNamespace and oDescendant.oIconFile and oDescendant.oIconFile.sName == sIconFileName:
          return gfoCreateResponseForRequestAndFile(oRequest, oDescendant.oIconFile);
    if sPath in oSelf.doFile_by_sRelativeURL:
      return gfoCreateResponseForRequestAndFile(oRequest, oSelf.doFile_by_sRelativeURL[sPath]);
    # handle tree data JSON
    if sPath == "/dxTreeData.json":
      oResponse = oRequest.foCreateReponse(
        uStatusCode = 200,
        sMediaType = gsJSONMediaType,
        sBody = oSelf.fsGetTreeDataJSON(),
      );
      oSelf.fDiscardUserState();
      return oResponse;
    if sPath == "/stop":
      oSelf.fStop();
      return oRequest.foCreateReponse(
        uStatusCode = 200,
        sMediaType = gsTextMediaType,
        sBody = "Stopping",
      );
    
    # Path not found
    return oRequest.foCreateReponse(
      uStatusCode = 404,
      sMediaType = gsTextMediaType,
      sBody = "URL %s not found" % json.dumps(oRequest.sURL),
    );
