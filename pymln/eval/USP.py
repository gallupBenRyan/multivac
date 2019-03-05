
import argparse
import os
import re

from collections import OrderedDict 

from multivac import settings
from multivac.pymln.utils import Utils
from multivac.pymln.syntax import Article, Sentence, Token


class USP(object):
    vowels = set('a','e','i','o','u')
    allowedDeps = set('nn','amod','prep_of','num','appos')
    evalDir = ''
    resultDir = ''
    dataDir = ''
    
    qas = dict() # {Question: set(Answers)}
    rel_qs = OrderedDict() # {str: list(Questions)}
    rel_clustIdx = dict() # {str: int}
    
    # Library of tokens
    qForms = set()
    qLemmas = set()
    form_lemma = dict() # {str: set(str)}
    
    # Clusters, Argument Clusters, Parts
    headDep_clustIdxs = dict() # {(str,str): str}
    lemma_clustIdxs = dict() # {str: set(str)}
    clustIdx_depArgClustIdx = dict() # {int: {str: int}}
    arg_cis = dict() # {str: list(list(str))}
    ptId_clustIdxStr = dict() # {str: (int, str)}
    ptId_aciChdIds = dict() # {str: {int: set(str)}}
    ptId_parDep = dict() # {str: str}
    clustIdx_ptIds = dict() # {int: set(str)}
    
    id_sent = dict() # {str: str}
    id_article = dict() # {str: Article}

    def readQuestions():
        filename = USP.evalDir + "/questions.sbj.txt"

        with open(filename, "r") as f:
            line = f.readline()

            while line:
                line = line.trim()

                if len(line) == 0:
                    continue

                v = line[line.rfind(' ')+1:]
                q = line[len("What does "),line.rfind(' ')].trim().lower()

                if v not in USP.rel_qs:
                    USP.rel_qs[v] = list()

                qu = Question(v, q, 'nsubj')
                USP.rel_qs[v].append(qu)
                USP.qForms.update(q.split()+[v])

        return None

    def readMorph(aid=None, mfilename=None, ifilename=None):
        return None

    def readSents(aid=None, filename=None):
        idx = 0
        with open(filename, "r") as f:
            line = f.readline()

            while line:
                line = line.trim()

                if len(line) == 0:
                    continue
                else:
                    idx += 1
                    sid = aid + ":" + str(idx)
                    USP.id_sent[sid] = line

        return None

    def readPart(filename):
        return None

    def procRelType(clustIdx, pos, relType):
        if relType in USP.rel_qs and pos == 'V':
            USP.rel_clustIdx[relType] = clustIdx

        if relType in USP.qLemmas:
            if relType not in USP.lemma_clustIdxs:
                USP.lemma_clustIdxs[relType] = set()

            USP.lemma_clustIdxs[relType].add(str(clustIdx))

        return None

    def readClust(filename):
        currCi = -1
        dep_aci = dict()

        with open(filename, 'r') as f:
            line = f.readline()

            while line:
                if not line[0].isdigit():
                    #do stuff
                else:
                    line = re.split("\W+", line)
                    ci = int(line[0])
                    pos, rt = line[1:3]
                    USP.procRelType(ci, pos, rt)




        return None

    def printAns(answer_file='Answers.txt'):
        with open('{}/Answers.txt'.format(USP.evalDir), 'w') as f:        
            for q, a_s in USP.qas.items():
                for ans in a_s:
                    sid = ans.getSentId()
                    sent = USP.id_sent[sid]
                    out  = "<question str=\"{}\">\n".format(q)
                    out += "<answer>{}</answer>\n".format(ans.getRst())
                    out += "<sentence id=\"{}\">{}</sentence>\n".format(sid,
                                                                      sent)
                    out += "</question>\n\n"

                    f.write(out)

        return None

    def getTreeStr(ptId):
        id_str = OrderedDict()

        if ptId in USP.ptId_aciChdIds:
            for cids in USP.ptId_aciChdIds[ptId]:
                for cid in cids:
                    if USP.ptId_parDep[cid] not in USP.allowedDeps:
                        continue

                    id_str[cid] = s + USP.getTreeStr(cid)

        id_str[ptId] = str(USP.ptId_clustIdxStr[ptId][0])

        x = ' '.join(id_str)

        return x

    def getTreeStrOld(ptId):
        id_str = OrderedDict()

        if ptId in USP.ptId_aciChdIds:
            for cids in USP.ptId_aciChdIds[ptId]:
                for cid in cids:
                    if USP.ptId_parDep[cid] not in USP.allowedDeps:
                        continue

                    if USP.ptId_parDep[cid].startswith('prep_'):
                        s = USP.ptId_parDep[cid].replace('prep_','')+' '
                    else:
                        s = ''

                    id_str[cid] = s + USP.getTreeStrOld(cid)

        x = ' '.join(id_str)

        return x

    def contains(cs, c):
        if isinstance(cs, list):
            return any([USP.contains(cs_i, str(c)) for cs_i in cs])
        else:
            return c in cs.split()

    def update_odict_all_cids(l, ptId, odict):
        if ptId in USP.ptId_aciChdIds:
            for cids in USP.ptId_aciChdIds[ptId]:
                for cid in cids:
                    if USP.ptId_parDep[cid] not in USP.allowedDeps:
                        continue

                    odict.update(l(cid))
    
        return odict

    def getTreeCis(ptId):
        cis = OrderedDict()
        cis[USP.ptId_clustIdxStr[ptId][0]] = 1

        if ptId in USP.ptId_aciChdIds:
            for cids in USP.ptId_aciChdIds[ptId]:
                for cid in cids:
                    if USP.ptId_parDep[cid] not in USP.allowedDeps:
                        continue

                    cis = cis.update(USP.getTreeCis(cid))

        return cis

    def isMatchFromHead(chdPtId, cis):
        hci = USP.ptId_clustIdxStr[chdPtId][0]

        if hci not in cis:
            return False

        tcis = USP.getTreeCis(chdPtId)

        for x in cis:
            ts = x.split()
            if set(tcis).isdisjoint(ts):
                return False

        return True

    def isMatch(chdPtId, arg):
        allcis = USP.arg_cis[arg]
        
        for cis in allcis:
            if USP.isMatchFromHead(chdPtId, cis):
                return True

        if chdPtId in USP.ptId_aciChdIds:
            for cids in USP.ptId_aciChdIds[chdPtId].values():
                for cid in cids:
                    dep = USP.ptId_parDep[cid]

                    if (dep.startswith('conj') and not dep=='conj_negcc') or \
                            dep == 'appos':
                        for cis in allcis:
                            if USP.isMatchFromHead(cid, cis):
                                return True

        return False

    def match():
        for rel, qs in USP.rel_qs.items():
            ci = USP.rel_clustIdx[rel]
            pids = USP.clustIdx_ptIds[ci]

            for q in qs:
                if q.getDep() == 'nsubj':
                    dep2 = 'dobj'
                else:
                    dep2 = 'nsubj'

                aci  = USP.clustIdx_depArgClustIdx[ci][q.getDep()]
                aci2 = USP.clustIdx_depArgClustIdx[ci][dep2]

                for pid in pids:
                    USP.match_q(q, pid, aci, aci2)

        return None

    def match_q(q, pid, aci, aci2):
        if pid not in USP.ptId_aciChdIds:
            return None
        elif: any([x not in USP.ptId_aciChdIds[pid] for x in (aci, aci2)]):
            return None

        for x, cids in USP.ptId_aciChdIds[pid].items():
            if x == aci or x == aci2:
                continue
            else:
                if any([USP.ptId_parDep[cid] == 'neg' for cid in cids]):
                    return None

        isMatch = False

        for cid in USP.ptId_aciChdIds[pid][aci]:
            if USP.isMatch(cid, q.getArg()):
                isMatch = True
                break

        if isMatch:
            for cid in USP.ptId_aciChdIds[pid][aci2]:
                USP.findAns(q, cid)

        return None


    def getSentId(ptId):
        return ptId[:ptId.rfind(':')]

    def getArticleId(ptId):
        return ptId[:ptId.lfind(':')]

    def getSentIdx(ptId):
        return ptId[ptId.lfind(':')+1:ptId.rfind(':')]

    def getTknIdx(ptId):
        return int(ptId[ptId.rfind(':')+1:])

    def findAns(q, pid):
        sid = USP.getSentId(pid)
        aid = USP.getArticleId(pid)
        sIdx = USP.getSentIdx(pid)
        art = USP.id_article[aid]
        sent = art._sentences[sIdx]

        pid_minPid = dict()

        ans = USP.findAnsPrep(pid, pid_minPid)

        for a in ans:
            na = OrderedDict()
            idx_prep = OrderedDict()

            for i in a:
                tknIdx = USP.getTknIdx(i)
                na.add(tknIdx)

                detIdx = -1

                if tknIdx in sent._tkn_children:
                    for depChd in sent._tkn_children[tknIdx]:
                        if depChd[0] == 'det':
                            detIdx = depChd[1]
                            na[detIdx] = 1
                            break

                if tknIdx in sent._tkn_par:
                    par = sent._tkn_par[tknIdx]
                    if par[0].startswith('prep_'):
                        parIdx = par[1]
                        parId = Utils.genTreeNodeId(aid, sIdx, parIdx)

                        if a.contains(parId):
                            prep = par[0].replace('prep_','')
                            mpid = pid_minPid[i]
                            midx = USP.getTknIdx(mpid)

                            if detIdx >= 0 and detIdx < midx:
                                midx = detIdx

                            idx_prep[midx] = prep

            s = ''

            for i in na:
                if len(idx_prep) > 0:
                    pidx = idx_prep[next(iter(idx_prep))]

                    if i >= pidx:
                        s = ' '.join([s, idx_prep.popitem(last=False)]).strip()

                word = sent._tokens[i].getForm()
                xid = Utils.genTreeNodeId(aid, sIdx, i)

                if xid in USP.ptId_clustIdxStr:
                    xs = USP.ptId_clustIdxStr[xid][1]

                    if ' ' in xs:
                        word = xs

                s = ' '.join([s, word]).strip()

            if q not in USP.qas:
                USP.qas[q] = set()

            USP.qas[q].add(Answer(sid, s))

        return None


    def findAnsPrep(pid, pid_minPid):
        ans = list()
        curr = list()
        z = OrderedDict()
        z[pid] = 1
        curr.append(z)
        pid_minPid[pid] = pid

        if pid in USP.ptId_aciChdIds:
            for cids in USP.ptId_aciChdIds[pid].values():
                for cid in cids:
                    dep = USP.ptId_parDep[cid]

                    if (dep.startswith('conj') and not dep=='conj_negcc') or \
                            dep == 'appos':
                        y = findAnsPrep(cid, pid_minPid)
                        ans += y

                        if Utils.compareStr(pid_minPid[cid], pid_minPid[pid]) < 0:
                            pid_minPid[pid] = pid_minPid[cid]
                    elif dep in USP.allowedDeps:
                        curr1 = list()
                        y = findAnsPrep(cid, pid_minPid)

                        if Utils.compareStr(pid_minPid[cid], pid_minPid[pid]) < 0:
                            pid_minPid[pid] = pid_minPid[cid]

                        for a in curr:
                            for b in y:
                                c = OrderedDict(list(a.items())+list(b.items()))
                                curr1.append(c)
                        curr = curr1

        ans.append(curr)

        return ans

    def preprocArgs():
        for r, qs in USP.rel_qs.items():
            ignoredQs = set()

            for q in qs:
                if q.getArg() in USP.arg_cis:
                    continue

                cis = list()
                x = list()
                ts = q.getArg().split()
                isIgnored = False

                for f in ts:
                    if f in ['the','of','in']:
                        continue

                    z = OrderedDict()

                    if f not in USP.form_lemma:
                        isIgnored = True
                        break

                    for l in USP.form_lemma[f]:
                        if l in USP.lemma_clustIdxs:
                            z = z.update(USP.lemma_clustIdxs[l])

                    s = ' '.join(z)
                    x.append(s)

                if isIgnored:
                    ignoredQs.add(q)
                    continue

                cis.append(x)

                if len(ts) >= 2:
                    z = OrderedDict()
                    hs = USP.form_lemma[ts[-1]]
                    ds = USP.form_lemma[ts[-2]]

                    for h in hs:
                        for d in ds:
                            if (h, d) in USP.headDep_clustIdxs:
                                z[USP.headDep_clustIdxs[(h, d)]] = 1

                    if len(z) > 0:
                        y = x[:-2]
                        y.append(' '.join(z))
                        cis.append(y)

                USP.arg_cis[q.getArg()] = cis

            qs = [x for x in qs if x not in ignoredQs]

        return None

    def removeThirdPerson(v):
        if v[-2] != 'e':
            pass
        elif v[-3] == 'i':
            v = v[:-3]+'y'
        elif v[-4:-2] == 'ss' or v[-4:-2] == 'sh':
            v = v[:-2]

        return v


def run():
    fid = os.path.basename(os.path.dirname(USP.dataDir))
    cl_file = "{}/{}.mln".format(USP.results_dir, fid)
    pr_file = "{}/{}.parse".format(USP.results_dir, fid)

    USP.readQuestions()
    USP.readMorph()
    USP.readClust(cl_file)
    USP.readPart(pr_file)
    USP.readSents()
    USP.preprocArgs()
    USP.match()
    USP.printAns()

    return None

if __name__ == '__main__':
    prs = argparse.ArgumentParser(description='Answer questions using an MLN '
                                     'knowledge base. \n'
                                     'Usage: python -m USP.py [-d data_dir] '
                                     '[-r results_dir] [-e eval_dir]')
    prs.add_argument('-d', '--data_dir', 
                        help='Directory of source files. If not specified, '
                        'defaults to the current working directory.')
    prs.add_argument('-r', '--results_dir', 
                        help='Directory to save results files. If not specified,'
                        ' defaults to the current working directory.')
    prs.add_argument('-p', '--eval_dir', 
                        help='Directory for evaluation files. If not specified,'
                        ' defaults to the current working directory.')
    prs.add_argument('-c', '--priorNumConj', 
                        help='Prior on number of conjunctive parts assigned to '
                        'same cluster. If not specified, defaults to 10.')

    args = vars(prs.parse_args())

    # Default argument values
    params = {'eval_dir': settings.eval_dir,
              'data_dir': settings.data_dir,
              'results_dir': settings.results_dir}

    # If specified in call, override defaults
    for par in params:
        if args[par] is not None:
            params[par] = args[par]

    if os.path.isabs(params['data_dir']):
        USP.dataDir = params['data_dir']
    else:
        USP.dataDir = os.path.join(os.getcwd(), params['data_dir'])

    if os.path.isabs(params['results_dir']):
        USP.resultDir = params['results_dir']
    else:
        USP.resultDir = os.path.join(os.getcwd(), params['results_dir'])

    if os.path.isabs(params['eval_dir']):
        USP.evalDir = params['eval_dir']
    else:
        USP.evalDir = os.path.join(os.getcwd(), params['eval_dir'])

    run()
