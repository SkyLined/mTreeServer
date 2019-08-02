import json, os;
from mHTTP import cHTTPServer, cURL, fsGetMediaTypeForExtension;

gsIndexHTMLFilePath = os.path.join(os.path.dirname(__file__), "index.html");
gsJSONMediaType = fsGetMediaTypeForExtension("json");
gsTextMediaType = fsGetMediaTypeForExtension("txt");

def fCheckIfIdIsUsedInTreeForNode(sId, oRootNode, oNode):
  oExistingNodeWithId = oRootNode.foGetNodeById(sId)
  assert oExistingNodeWithId is None, \
      "%s cannot have id %s because it is already used in the tree by %s" % (oNode.sName, sId, oExistingNodeWithId.sName);

def foCreateResponseForRequestAndFilePath(oRequest, sFilePath):
  oFile = open(sFilePath, "rb");
  try:
    sFileContent = oFile.read();
  finally:
    oFile.close();
  return oRequest.foCreateReponse(
    uStatusCode = 200,
    sMediaType = fsGetMediaTypeForExtension(sFilePath),
    sBody = sFileContent,
  );


class cTreeNode(object):
  def __init__(oSelf, sName, sType = None, sData = None, sId = None, sIconFileName = None, bOpened = None, bDisabled = None, bSelected = None):
    oSelf.sName = sName;
    oSelf.sType = sType;
    oSelf.sData = sData;
    oSelf.__sId = sId;
    oSelf.sIconFileName = sIconFileName;
    oSelf.bOpened = bOpened;
    oSelf.bDisabled = bDisabled;
    oSelf.bSelected = bSelected;
    oSelf.__oParentNode = None;
    oSelf.__aoChildNodes = [];
  
  def foCreateChildNode(oSelf, sName, **dxAdditionalArguments):
    oChildNode = cTreeNode(sName, **dxAdditionalArguments);
    oSelf.fAppendChild(oChildNode);
    return oChildNode;
  
  @property
  def sId(oSelf):
    assert oSelf.__sId, \
        "%s does not have an id" % oSelf.sName;
    return oSelf.__sId;
  @sId.setter
  def sId(oSelf, sId):
    assert oSelf.__sId is None, \
        "%s already has an id" % oSelf.sName;
    fCheckIfIdIsUsedInTreeForNode(sId, oSelf.oRootNode, oSelf);
    oSelf.__sId = sId;
  
  def fLinkToNode(oSelf, oTargetTreeNode):
    # Make sure oTargetTreeNode is part of the same tree as oSelf.
    aoOwnChainToRootNodes = [];
    oOwnChainToRootNode = oSelf;
    while oOwnChainToRootNode:
      aoOwnChainToRootNodes.append(oOwnChainToRootNode);
      oOwnChainToRootNode = oOwnChainToRootNode.__oParentNode;
    oTargetChainToRootNode = oTargetTreeNode;
    while oTargetChainToRootNode not in aoOwnChainToRootNodes:
      oTargetChainToRootNode = oTargetChainToRootNode.__oParentNode;
      assert oTargetChainToRootNode is not None, \
          "Cannot link to a node that is not part of the same tree";
    oSelf.sType = "node-link";
    oSelf.sData = oTargetTreeNode.sId;
  
  def fLinkToNodeId(oSelf, sTargetId):
    # No sanity checks; can be used to link to nodes that will be added to the
    # tree later.
    oSelf.sType = "node-link";
    oSelf.sData = sTargetId;
  
  def foGetNodeById(oSelf, sId):
    if oSelf.__sId == sId: return oSelf;
    for oChild in oSelf.__aoChildNodes:
      oNode = oChild.foGetNodeById(sId);
      if oNode: return oNode;
    return None;
  
  @property
  def oParentNode(oSelf):
    return oSelf.__oParentNode;

  @property
  def oRootNode(oSelf):
    # Ascend to the root node.
    oAscendingNode = oSelf;
    while oAscendingNode.__oParentNode:
      oAscendingNode = oAscendingNode.__oParentNode;
    return oAscendingNode;
  
  @property
  def aoChildNodes(oSelf):
    return oSelf.__aoChildNodes[:];
  
  def fRemoveChild(oSelf, oChildNode):
    assert oChildNode in oSelf.__aoChildNodes, \
        "%s is not a child of %s" % (oChildNode.sName, oSelf.sName);
    oSelf.__aoChildNodes.remove(oChildNode);
    oChildNode.__oParentNode = None;
  
  def fRemove(oSelf):
    assert oSelf.__oParentNode, \
        "%s does not have a parent" % oSelf.sName;
    oSelf.__oParentNode.fRemoveChild(oSelf);
  
  def fAppendChild(oSelf, oChildNode):
    assert oChildNode.__oParentNode is None, \
        "%s already has a parent" % oSelf.sName;
    if oChildNode.__sId:
      fCheckIfIdIsUsedInTreeForNode(oChildNode.__sId, oSelf.oRootNode, oChildNode);
    oSelf.__aoChildNodes.append(oChildNode);
    oChildNode.__oParentNode = oSelf;
  
  def fDiscardUserState(oSelf):
    oSelf.bOpened = None;
    oSelf.bSelected = None;
    for oChildNode in oSelf.__aoChildNodes:
      oChildNode.fDiscardUserState();
  
  def fdxGetJSON(oSelf):
    dxJSON = {"text": oSelf.sName};
    bForceDisabled = False;
    if oSelf.sType:
      dxJSON["data"] = {
        "sType": oSelf.sType,
        "sData": oSelf.sData,
      };
      if oSelf.sType == "node-link" and not oSelf.oRootNode.foGetNodeById(oSelf.sData):
        bForceDisabled = True;
    if oSelf.__sId is not None:
      dxJSON["id"] = oSelf.__sId;
    if oSelf.sIconFileName is not None:
      dxJSON["icon"] = "/icons/%s" % oSelf.sIconFileName;
    if oSelf.__aoChildNodes:
      dxJSON["children"] = [
        oChildNode.fdxGetJSON()
        for oChildNode in oSelf.__aoChildNodes
      ];
    dxStateJSON = {};
    if oSelf.bOpened is not None:
      dxStateJSON["opened"] = oSelf.bOpened;
    if bForceDisabled:
      dxStateJSON["disabled"] = True;
    elif oSelf.bDisabled is not None:
      dxStateJSON["disabled"] = oSelf.bDisabled;
    if oSelf.bSelected is not None:
      dxStateJSON["selected"] = oSelf.bSelected;
    if len(dxStateJSON) != 0:
      dxJSON["state"] = dxStateJSON;
    return dxJSON;

class cTreeServer(cTreeNode, cHTTPServer):
  def __init__(oSelf, sName, sType = None, sData = None, **dxHTTPServerArguments):
    oSelf.__bComplete = False;
    oSelf.__sIconsFolderPath = None;
    cTreeNode.__init__(oSelf, sName, sType, sData);
    cHTTPServer.__init__(oSelf, **dxHTTPServerArguments);
  
  @property
  def sIconsFolderPath(oSelf):
    return oSelf.__sIconsFolderPath;
  
  @sIconsFolderPath.setter
  def sIconsFolderPath(oSelf, sIconsFolderPath):
    assert oSelf.__sIconsFolderPath is None, \
        "Cannot set icons folder path twice!";
    if sIconsFolderPath[-1:] != os.sep:
      sIconsFolderPath += os.sep;
    assert os.path.isdir(sIconsFolderPath), \
        "Cannot find folder %s" % sIconsFolderPath;
    oSelf.__sIconsFolderPath = sIconsFolderPath;
  
  def fComplete(oSelf):
    oSelf.__bComplete = True;
  
  def fStart(oSelf):
    cHTTPServer.fStart(oSelf, oSelf.__fRequestHandler);
  
  def __fRequestHandler(oSelf, oSelf2, oConnectionFromClient, oRequest):
    # Filter out invalid methods
    if oRequest.sMethod.upper() != "GET":
      return oRequest.foCreateReponse(
        uStatusCode = 405,
        sMediaType = gsTextMediaType,
        sBody = "Method %s not allowed" % json.dumps(oRequest.sMethod),
      );
    
    oURL = oSelf.foGetRequestURL(oRequest);
    # handle index HTML
    if oURL.sPath == "/":
      return foCreateResponseForRequestAndFilePath(oRequest, gsIndexHTMLFilePath);
    # handle icons
    if oSelf.__sIconsFolderPath and oURL.sPath.startswith("/icons/"):
      sIconFilePath = os.path.realpath(os.path.join(oSelf.__sIconsFolderPath, oURL.sPath[7:]));
      # prevent directory traversal
      if os.path.commonprefix([sIconFilePath, oSelf.__sIconsFolderPath]) == oSelf.__sIconsFolderPath: 
        if os.path.isfile(sIconFilePath):
          return foCreateResponseForRequestAndFilePath(oRequest, sIconFilePath);
          
    # handle tree data JSON
    if oURL.sPath == "/dxTreeData.json":
      oResponse = oRequest.foCreateReponse(
        uStatusCode = 200,
        sMediaType = gsJSONMediaType,
        sBody = json.dumps({
          "dxRootTreeNode": oSelf.fdxGetJSON(),
          "nNextRefreshTimeoutInSeconds": None if oSelf.__bComplete else 1,
        }),
      );
      oSelf.fDiscardUserState();
      return oResponse;
    if oURL.sPath == "/stop":
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
