# 詰将棋ソルバーエンジン　Ver.2(無駄合い検証)＋MapDic(局面マップ)＋ShortCut（冗長手順削除）版

from operator import itemgetter

try:    #　CythonのDLL(shogi_cy*.pyd)がimport可能なときは使う、ダメならPythonを使う
    from shogi_cy import fst,snd,mix,Shogi
    print("⚡⚡Using Shogi from shogi_cy.pyd")
except:
    from shogi import fst,snd,mix,Shogi
    print("■Using Shogi from shogi.py")
from MyUtils import StopWatch

try:    #　CythonのDLL(SolverUtils_cy*.pyd)がimport可能なときは使う、ダメならPythonを使う
    from SolverUtils_cy import Shogi_Operation,SearchOute
    print("⚡⚡⚡SolverUtils_cy imported!!")
except:
    from SolverUtils import Shogi_Operation,SearchOute

# ソルバークラス　DFM・無駄合い検証・詰み手順マッピング・冗長手順削除
class TsumeSolver2mdsc:
    
    def __init__(self):
        self.MaxStep=1
        self.dictop={}
        self.TotalCnt=0
        self.progress=True

    # **現在不使用** 反復深化深さ優先探索(IDDFS)　トップ
    def Solve_IdDfs(self, shogi, Maxstep):
        print("TsumeSolver3(IDDFS) is called!!")
        print(f"  initial:{str(shogi)}, N = {Maxstep}")
        self.MapDic = {}
        self.TotalCnt=0
        countdic = {}

        for i in range(1,Maxstep+1,2):
            ret = self.Solve_Dfs(shogi, i)
            countdic[i]=self.TotalCnt
            if ret:
                for ii in countdic:
                    print(f"探索深さ:{ii} , 探索手数：{countdic[ii]} ")
                #デバッグ：MapDicキー一覧
                # print("デバッグ：MapDicキー一覧")
                # for key in self.MapDic:
                #     print(f"key={key}")
                
                self.remove_redundancy(shogi,self.dictop)
                self.reorganize_dic(shogi,self.dictop,0)

                return True
        return False


    #DFS+無駄合い検証+冗長手順削除　トップ
    def Solve_mdsc(self, shogi, Maxstep):
        print("TsumeSolver2mdsc is called!!")
        print(f"  initial:{str(shogi)}, N = {Maxstep}")
        self.MapDic = {}
        self.TotalCnt=0

        sw = StopWatch(n_round=3).start()

        #ソルバー起動
        ret = self.Solve_Dfs(shogi, Maxstep)
        if ret:
            #デバッグ：MapDicキー一覧
            # print("デバッグ：MapDicキー一覧")
            # for key in self.MapDic:
            #     print(f"key={key}")
            sw.end().show(label='探索終了')

            # # 不具合調査
            # with open("dic_debug0705_original.txt" , "w", encoding="utf-8") as fp:
            #     self.HierPrintDic(fp=fp)
    
            #　MapDicを用いた冗長手順削除
            self.remove_redundancy(shogi,self.dictop)
            sw.end().show(label='冗長手順削除完了')

            # # 不具合調査
            # with open("dic_debug0705_before_reorganize.txt" , "w", encoding="utf-8") as fp:
            #     self.HierPrintDic(fp=fp)

            #　正解dictionaryの再構築
            self.reorganize_dic(shogi,self.dictop,0)
            sw.end().show(label='ツリー再構築完了')

            # #不具合調査
            # with open("dic_debug0705_after_reorganize.txt" , "w", encoding="utf-8") as fp:
            #     self.HierPrintDic(fp=fp)


            return True
        return False

    # DFS本体　Solve_mdscから呼ばれる。
    def Solve_Dfs(self,shogi,MaxStep):

        self.dictop={}
        self.MaxStep=MaxStep
        #self.TotalCnt=0
        count=0
        fisrtCands = self.searchOute(shogi)
        fisrtCands2 = self.__changeOrder(count,fisrtCands,shogi)
    
        if self.progress:
            print('初手候補',len(fisrtCands),':',fisrtCands)
    
        for iCand in fisrtCands2:
            dic={}
            ret=self.__VerifyOuteCandidate(count,shogi,iCand,dic)
            if self.progress:
                print('  ',iCand,'検証結果：',ret,'count',self.TotalCnt)
            if ret:     #ひとつ成功を見つけたらループ終了
                #print(DBG,'SolverTop2', iCand,'success, dic=',dic)
                self.dictop['next']=[iCand]
                self.dictop[iCand]=dic
                return True
        return False #この手数では詰まなかった。
    
    # 詰み手順マップ（MapDic)を使って冗長手順を削除する
    def remove_redundancy(self,shogi, dic):
   
        if not dic['next']:
            return

        for oute in dic['next']:
            dic1 = dic[oute]
            shogi_oute = Shogi()
            shogi.copyto(shogi_oute)
            shogi_oute.DoOperation(oute)

            for uke in dic1['next']:

                shogi_uke = Shogi()
                shogi_oute.copyto(shogi_uke)
                shogi_uke.DoOperation(uke)
                key = str(shogi_uke)
                keys_subset = shogi_uke.generate_fullkey_subsets(key)

                shortcut = None
                for key_sub in keys_subset:
                    if key_sub in self.MapDic:
                        # shortcut =self.MapDic[key_sub] 不具合0521修正
                        depth,mdic = self.MapDic[key_sub] #depthは使わない
                        shortcut = self.copy_dic(mdic)
                        print(f"Solver.remove_redundancy: found_shortcut in {key_sub}")
                        break
                if shortcut:
                    dic1[uke] = shortcut
                    continue

                dic2 = dic1[uke]
                self.remove_redundancy(shogi_uke,dic2)
        return

    # (1)冗長手削除によって壊れた手数をカウントし直す　(2)持ち駒の使い切り、先手盤上駒数を記録する
    def reorganize_dic(self,shogi:Shogi,dic,count):
        count +=1

        nexts = list(dic['next']) # ループの中で要素を削除する可能性があるので、コピーしておく
        for ope in nexts:
            dic1 = dic[ope]
            dic1['cnt']=count
            shogi1 = Shogi()
            shogi.copyto(shogi1)

            try:
                shogi1.DoOperation(ope)
            except:
                # 不具合対応 2026.7.2　★ 不正な後手の打ち駒だけ削除する ★
                # remove_redndancyの副作用で後手が持っていない合いゴマが候補手に入ってしまうことあり。
                if ope.isUchi and ope.owner == snd:
                    dic['next'].remove(ope)
                    del dic[ope]
                    continue
                else:
                    # 先手の打ち駒や通常手で例外が出るのは異常なので raise
                    raise

            if dic1['next'] == []:
                dic1['empty']=shogi1.isDaiEmpty(fst)
                dic1['n_fst']=len(shogi1.kban[fst])
                # print(f"  shogi:{str(shogi1)}, empty:{dic1['empty']}")

            self.reorganize_dic(shogi1,dic1,count)
        
        return

    # 詰将棋検証用のパブリック王手検証メソッド
    def VerifyOuteCand(self,count,shogi:Shogi,Cand,dict):
        return self.__VerifyOuteCandidate(count,shogi,Cand,dict)

    # 王手の検証：王手に対する応手がないとき、またはすべての応手が失敗したときにTrueをかえし、それ以外はFalseを返す。
    def __VerifyOuteCandidate(self,count,shogi:Shogi,Cand,dict,check_muda=False,limit_depth=0):

        # 通常はself.MaxStepを使用、無駄合い検証中なら引数を使う。
        max_step = limit_depth if limit_depth else self.MaxStep

        count += 1
        self.TotalCnt += 1

        #DEBUG UndoOperation不具合　list.remove(x): x not in list
        # print(f"__VerifyOuteCandidate cout:{count},Cand:{Cand},muda:{check_muda},limit:{limit_depth}")

        # shogitmp=Shogi()
        # shogi.copyto(shogitmp)
        shogitmp = shogi #高速化のためCopyやめてUndoを使う！
        shogitmp.DoOperation(Cand)

        ukeCands,mudaCands = self.searchUke(shogitmp)
        if self.progress and count==1:
            print('  ',Cand,'受け候補手',len(ukeCands),':',ukeCands)
        if ukeCands==[]:
            if Cand.char=='歩' and Cand.isUchi:
                shogi.UndoOperation(Cand)
                return False    #打ち歩詰めは失敗
            #　ここでは詰み判定をしない。ukeCandだけでなく、mudaCandsも含めた詰み判定を下のコードで行う。

        elif count == max_step: #手数になったが詰まなかった→MaxStepの次の受け手があったとき
            shogi.UndoOperation(Cand)
            return False
        elif count > max_step:
            shogi.UndoOperation(Cand)
            raise Exception(f"__VerifyOuteCandidate: count:{count},max_step:{max_step},check_muda:{check_muda}")
       
        #王手候補手Candに対して、すべての受け候補ukaCnadを検証する。すべての受けが失敗すればCandは成功、ひとつでもukeCandが成功すればCandは失敗
        localdict={}
        for uke_cand in ukeCands:
            ukedic = {}
            ukeret = self.__verifyUkeCandidate(count,shogitmp,uke_cand,ukedic,check_muda=check_muda,limit_depth=limit_depth)

            if ukeret: #受け候補手のひとつでも成功したら
                shogi.UndoOperation(Cand)
                return False
            else:
                localdict[uke_cand]=ukedic

        #無駄合い検証　すべての受けが失敗した場合・　無駄合い検証中の無駄合い検証はしない（バグ防止のため）          
        valid_cands = []
        if mudaCands and not check_muda:
            # print("VerifyOuteCandidate: 無駄合い検証")

            # 受けの最善手での詰み手数を改めて探す。 →　探索手数が増える？　→IDDFS化により、局所IDDFSを廃止
            muda_localdict={}
            for uke_cand in ukeCands:
                for depth in range(count+2,self.MaxStep+1,2):
                    ukedic = {}
                    ukeret = self.__verifyUkeCandidate(count,shogitmp,uke_cand,ukedic,limit_depth=depth)
                    if not ukeret:
                        muda_localdict[uke_cand]=ukedic
                        break

            cur_depth = self.__getDepth(muda_localdict,ukeCands,count)
            valid_cands = self.__validateMudaCands(count,shogitmp,mudaCands,cur_depth)
            if valid_cands and count == max_step: #手数になったが詰まなかった→MaxStepの次の受け手があったとき
                shogi.UndoOperation(Cand)
                return False
            for uke_cand in valid_cands:
                # print(f"有効中合い：{uke_cand}")
                ukedic = {}
                ukeret = self.__verifyUkeCandidate(count,shogitmp,uke_cand,ukedic)

                if ukeret: #受け候補手のひとつでも成功したら
                    shogi.UndoOperation(Cand)
                    return False
                else:
                    localdict[uke_cand]=ukedic

        #応手候補手がすべて失敗し、有効中合いなし、もしくは有効中合いもすべて失敗した場合
        dict['cnt']=count
        dict['success']=True
        dict['next']=valid_cands + ukeCands
        #正解手順（持ち駒使い切り）ならば印をつける。
        if not check_muda and count == max_step and shogitmp.isDaiEmpty(fst):
            dict['empty']=True
        dict.update(localdict)
        
        #高速化のためCopyやめてUndoを使う！
        shogi.UndoOperation(Cand)

        return True

   # 応手の検証：応手に対して王手がないとき、またはすべての王手が失敗したときにTrueをかえし、それ以外はFalseを返す。
    def __verifyUkeCandidate(self,count,shogi:Shogi,def_cand,dict,check_muda=False,limit_depth=0):
        self.TotalCnt += 1
        count+=1

        # #DEBUG UndoOperation不具合　list.remove(x): x not in list
        # print(f"__verifyUkeCandidate cout:{count},Cand:{def_cand},muda:{check_muda},limit:{limit_depth}")

        #高速化のためCopyやめてUndoを使う！
        # tmp_shogi = Shogi()
        # shogi.copyto(tmp_shogi)
        tmp_shogi = shogi
        tmp_shogi.DoOperation(def_cand)

        # MapDicに局面があれば（すでに詰み筋があれば）、この知見を利用する。
        use_cashe = not check_muda
        key = str(tmp_shogi)
        # 探索時はMapDicを使うのやめる。作るだけにする。
        # 手数超過不具合調査の対応としてコメントアウト。探索中はMapDic使わない
        if use_cashe and key in self.MapDic:
            depth,mdic = self.MapDic[key]
            if count<=depth: #階層がより深い詰筋のみを利用する。
                dict.update(self.copy_dic(mdic))
                shogi.UndoOperation(def_cand)
                return False

        OuteCands = self.searchOute(tmp_shogi)

        for oute_cand in OuteCands:
            retdic={}
            ret_Oute = self.__VerifyOuteCandidate(count,tmp_shogi,oute_cand,retdic,check_muda=check_muda,limit_depth=limit_depth)
            if ret_Oute:
                dict[oute_cand]=retdic
                dict['cnt']=count
                dict['next']=[oute_cand]
                dict['success']=False

                # 王手成功（詰み筋）のときは、MapDicに知見を格納する
                if use_cashe:
                    # #debug
                    # if key=="飛52,歩82,桂63,歩64|桂70,玉80,歩83|歩0,香0,桂0,銀0,金0,角0,飛0":
                    #     print(f"Saving_dict to MapDic:{dict}")
                    if not key in self.MapDic: #先に見つかったほうが短い手順なので上書きはしない。
                        self.MapDic[key]=(count,dict.copy()) #ここは浅いコピーでOK
                    else:
                        depth,mdic = self.MapDic[key]
                        if depth<count: #同じ局面でも手が深いところの（短い）詰み筋を優先する
                            self.MapDic[key] = (count,dict.copy())  #ここは浅いコピーでOK

                shogi.UndoOperation(def_cand)
                return False
            
        shogi.UndoOperation(def_cand)
        return True

    # 無駄合い検証：合いゴマ候補手のリストをもとに、有効合いゴマ（合いゴマによって詰み手順が＋2手以上になるもの）のリストを返す
    def __validateMudaCands(self,count,shogi,mudaCands,d_max):
        valid_cands = []
        
        for cell,lst_ope in mudaCands:
            # shogitmp = Shogi()
            # shogi.copyto(shogitmp)
            shogitmp = shogi
            shogitmp.DoOperation(lst_ope[0]) #一手しか検証しない。どうせ取られる駒なので。
            outeCands = self.__searchMoveOute_on_cell(shogitmp,cell)

            tsumi = False
            for oute_cand in outeCands:
                # 無駄検証モードで__VerifyOuteCandidateを呼ぶ、countはマイナス１する。
                result = self.__VerifyOuteCandidate(count-1,shogitmp,oute_cand,{},check_muda=True,limit_depth=d_max)
                if result:
                    tsumi = True
                    break

            if not tsumi:
                valid_cands+= lst_ope
            
            shogitmp.UndoOperation(lst_ope[0])
        
        return valid_cands
    
    def __getDepth(self,dict,UkeCands,count):

        #再帰関数の定義
        def find_depth(dict,count):
            count +=1
            lst_depth = []
            if dict['next']:
                for cand in dict['next']:
                    lst_depth.append(find_depth(dict[cand],count))
                return max(lst_depth)
            else:
                return count

        #メソッド処理
        if not dict:
            return count

        lst_depth = []
        for cand in UkeCands:
            lst_depth.append(find_depth(dict[cand],count))
        return max(lst_depth)

    def __changeOrder(self,count,cands,shogi):
        if count>=self.MaxStep-1:
            return cands
        
        count+=1
        pair_cands=[]
        for icand in cands:
            shgtmp=Shogi()
            shogi.copyto(shgtmp)
            shgtmp.DoOperation(icand)
            ukecands,mudacands=self.searchUke(shgtmp)
            
            pair_cands.append([icand,len(ukecands)])
        
        items_sorted = sorted(pair_cands, key=itemgetter(1))

        retcands=[]
        for i in items_sorted:
            retcands.append(i[0])

        return retcands

    # 可能なすべての王手のリストを返す（Cython高速化済み：SolverUtils_cy.cp312-win_amd64.pyd）
    def searchOute(self,shogi):

        return SearchOute(shogi)

    # *現在不使用:SolverUtilsに移動済み*　盤上の駒による王手のリストを返す
    def __searchMoveOute(self,shogi):
        OuteList = []

        # 盤上の先手駒のループ
        for ikoma in shogi.kban[fst]:
            rchlst = ikoma.rch
            rchlst = ListOperator.subList(rchlst,shogi.distrib[fst])
            # rchlst = set(rchlst)-distrib_f
            chkposlst = shogi.Gyoku.gen_chkposlst(ikoma.char,shogi.distrib[mix])
            chklst = ListOperator.andList(rchlst,chkposlst)
            # chklst = rchlst & chkposlst
            self.dbgprint('__searchMoveOute'+ikoma.char+str(chklst))

            #成王手を先にする
            if ikoma.pchar and not ikoma.ispromoted:
                chkposlst = shogi.Gyoku.gen_chkposlst(ikoma.pchar,shogi.distrib[mix])
                chkposlst = ListOperator.subList(chkposlst,shogi.distrib[fst])
                # chkposlst = set(chkposlst)-distrib_f
                chklst2 = ListOperator.andList(rchlst,chkposlst)
                # chklst2 = rchlst & chkposlst
            
                for ipos in chklst2:
                    if ikoma.pos[1]<3 or ipos[1]<3:
                        OuteList.append(Shogi_Operation(fst,False,ikoma.char,True,ikoma.pos,ipos))

            for ipos in chklst:
                if ipos == shogi.Gyoku.pos:
                    print('error')
                OuteList.append(Shogi_Operation(fst,False,ikoma.char,False,ikoma.pos,ipos))

        self.dbgprint('__searchMoveOute'+str(OuteList))
        return OuteList
    
    # 無駄合い検証のときのみ使用。合いゴマを取る王手のリストを返す。このメソッドを使用中！
    def __searchMoveOute_on_cell(self,Shogi,cell):
        OuteList = []
        x,y = cell
        komas = Shogi.ban[x][y].rch[fst] #cellに移動可能な駒のリスト

        for koma in komas:
            if koma.pos[1]<3 or cell[1]<3:  #成ることができる場所にいて
                if koma.pchar and not koma.ispromoted: #成ることができる場合
                    chkposlst = Shogi.Gyoku.gen_chkposlst(koma.pchar,Shogi.distrib[mix])
                    if cell in chkposlst:
                        OuteList.append(Shogi_Operation(fst,False,koma.char,True,koma.pos,cell))
            chkposlst = Shogi.Gyoku.gen_chkposlst(koma.char,Shogi.distrib[mix])
            if cell in chkposlst:
                OuteList.append(Shogi_Operation(fst,False,koma.char,False,koma.pos,cell))
        
        return OuteList

    # *現在不使用:SolverUtilsに移動済み*　駒を打つ王手のリストを返す
    def __searchUchiOute(self,Shogi):
        OuteList = []

        for ichar,komalist in Shogi.kdai[fst].items():
            if not komalist:
                continue
            # 以下、持ち駒あるとき、持ち駒種類ごとに王手を抽出
            if ichar == '歩' and Shogi.FuDic[fst][Shogi.Gyoku.pos[0]]:
                continue   #二歩防止のため、候補手に入れない。打ち歩詰め防止は__VerifyOuteCandidateの詰み判定にて実施
            #　王手可能位置
            chkposlst=Shogi.Gyoku.gen_chkposlst(ichar,Shogi.distrib[mix])
            chkposlst=ListOperator.subList(chkposlst,Shogi.distrib[mix])
            # chkposlst=set(Shogi.Gyoku.gen_chkposlst(ichar,Shogi.distrib[mix]))-distrib_m
            for ipos in chkposlst:
                OuteList.append(Shogi_Operation(fst,True,ichar,False,None,ipos))
        self.dbgprint('__searchUchiOute'+str(OuteList))

        return OuteList
    
    # *現在不使用:SolverUtilsに移動済み*　開き王手のリストを返す    
    def __searchHirakiOute(self,Shogi):
        OuteList = []
        for ikoma in Shogi.kban[fst]:
            flyer = self.__isBlocking(Shogi,ikoma)
            if flyer:
                waycells=flyer.getInnerCells(ikoma.pos)+flyer.getOuterCells(ikoma.pos)
                cells = ListOperator.subList(ikoma.rch,waycells+Shogi.distrib[fst])
                # cells = set(ikoma.rch) - set(waycells+Shogi.distrib[fst])

                for cell in cells:
                    if ikoma.pchar and not ikoma.ispromoted:    #成り優先
                        if ikoma.pos[1]<3 or cell[1]<3:
                            OuteList.append(Shogi_Operation(fst,False,ikoma.char,True,ikoma.pos,cell))

                    if ikoma.char == '香' and cell[1]==0: #香が1段に移動する際には成らなければならない
                        pass
                    elif ikoma.char=='桂' and cell[1]<2:    ##桂が1段・2段に移動する際には成らなければならない
                        pass
                    else:
                        OuteList.append(Shogi_Operation(fst,False,ikoma.char,False,ikoma.pos,cell))
        #移動王手と重複することあり→__serchOuteで重複チェックして削除する。

        return OuteList

    # 王手に対する応手のリストを返す
    def searchUke(self,shogi):
        lst_Tori = self.__searchToriUke(shogi)
        lst_Nige = self.__searchNigeUke(shogi)
        lst_aigoma,mudaCandsLst = self.__searchAigoma(shogi)
    
        self.dbgprint('__searchUke'+str(lst_Nige+lst_Tori+lst_aigoma))
        return lst_Tori+lst_Nige+lst_aigoma,mudaCandsLst

    # 玉が逃げる応手のリストを返す
    def __searchNigeUke(self,shogi):
        xg,yg=shogi.Gyoku.pos
        outeKomaLst = shogi.ban[xg][yg].rch[fst]
        outeKomaPosLst=[]
        for ikoma in outeKomaLst:
            outeKomaPosLst.append(ikoma.pos)
        
        poslst = []
        for ipos in shogi.Gyoku.rch:
            x,y= ipos
            if (shogi.ban[x][y].rch[fst]==[]) and not (ipos in shogi.distrib[snd]): #相手の効きがなく、味方のいないところ
                if ipos not in outeKomaPosLst:  #同玉はToriukeで考慮済み。
                    poslst.append(ipos)
        #print('Solver:__searchNigeUke  poslst=',poslst)
        
        #飛車角香の効き延長を考慮、移動先が効きの延長線上であれば、この移動先はリストposlstから削除する。
        xg,yg=shogi.Gyoku.pos
        okomalst = shogi.ban[xg][yg].rch[fst]
        lst_canfly=[]
        for iok in okomalst:
            if iok.canFly:
                lst_canfly.append(iok)
         
        if lst_canfly:
            for ikoma in lst_canfly:
                cells = ikoma.getOuterCells(shogi.Gyoku.pos)
                if cells and cells[0] in poslst:
                    poslst.remove(cells[0])

        UkeOpeList =[]
        for ipos in poslst:
            UkeOpeList.append(Shogi_Operation(snd,False,shogi.Gyoku.char,False,shogi.Gyoku.pos,ipos))

        #print('__searchNigeUke',UkeOpeList)
        return UkeOpeList        

    # 王手している駒を取る応手のリストを返す
    def __searchToriUke(self,shogi):
        UkeOpeList =[]
        xg,yg=shogi.Gyoku.pos
        otekomalst = shogi.ban[xg][yg].rch[fst]
        if len(otekomalst)>1:  #両王手で、同玉で大丈夫な場合
            for otekoma in otekomalst:
                xo,yo = otekoma.pos
                if otekoma.pos in shogi.Gyoku.rch and not shogi.ban[xo][yo].rch[fst]:
                    UkeOpeList.append(Shogi_Operation(snd,False,shogi.Gyoku.char,False,shogi.Gyoku.pos,otekoma.pos))
        elif len(otekomalst)==1:  #ダブル王手のときは、同玉以外に駒を取る受けはない。
            #print('王手している駒'+ str(otekomalst[0].pos)+ otekomalst[0].char)
            xc,yc=otekomalst[0].pos
            komaCandlst = shogi.ban[xc][yc].rch[snd]
            for icand in komaCandlst:
                #print('王手駒をとる', icand.char, icand.pos,[xc,yc])
                if icand == shogi.Gyoku:
                    if shogi.ban[xc][yc].rch[fst]:
                        continue       #攻め方の効きがある場合は同玉できない。
                #飛車角香の王手の道を開けてしまう場合を考慮する必要あり
                if self.__isBlocking(shogi,icand):
                    continue
                UkeOpeList.append(Shogi_Operation(snd,False,icand.char,False,icand.pos,otekomalst[0].pos))
                if icand.pchar and not icand.ispromoted:
                    if icand.pos[1]>5 or otekomalst[0].pos[1]>5:
                        UkeOpeList.append(Shogi_Operation(snd,False,icand.char,True,icand.pos,otekomalst[0].pos))

        #print('__searchToriUke',UkeOpeList)
        return UkeOpeList

    #　合いゴマする応手（移動合い含む）のリストと、無駄合い候補手（セル・候補手リストのリスト）を返す
    def __searchAigoma(self,shogi):
        idoUkeOpeList=[]
        UkeOpeList =[]

        xg,yg=shogi.Gyoku.pos
        otekomalst = shogi.ban[xg][yg].rch[fst]


        if len(otekomalst)!=1:  #ダブル王手のときは合い駒はできない
            return [],[]
        
        if not otekomalst[0].canFly:    # 飛車・角・香・龍・馬　以外の駒からの王手には合い駒なし
            return [],[]
        
        mudaAiCandsSet = []
        cells =otekomalst[0].getInnerCells(shogi.Gyoku.pos)
        mkomaCands = shogi.kdai[snd].keys()
        for cell in cells:
            mudaAiCands = []
            x,y=cell
            rchfst=shogi.ban[x][y].rch[fst].copy() #cellに効きを持つ先手駒オブジェクトのリスト
            rchsnd=shogi.ban[x][y].rch[snd].copy() #cellに効きを持つ後手駒オブジェクトのリスト
            for i in rchsnd.copy(): #あらかじめ後手効き駒リストからPinされている駒を削除しておく。
                if self.__isBlocking(shogi,i):
                    rchsnd.remove(i)

            #このセルに打てる合い駒リスト
            char_cands = []
            for mkoma in mkomaCands:
                if shogi.kdai[snd][mkoma]:
                    if mkoma =='歩' and shogi.FuDic[snd][cell[0]]:
                        continue
                    else:
                        char_cands.append(mkoma)
            
            numof_kiki = len(rchsnd)

            if numof_kiki == 0:
                for mkoma in char_cands:
                    mudaAiCands.append(Shogi_Operation(snd,True,mkoma,False,None,cell))
            elif numof_kiki == 1:
                kikikoma = rchsnd[0]
                if kikikoma == shogi.Gyoku and  len(rchfst)>=2: #無駄合い候補手、合いゴマ効かずかどうかは__VerifyOuteCandidateメソッドに任せる。
                    for mkoma in char_cands:
                        mudaAiCands.append(Shogi_Operation(snd,True,mkoma,False,None,cell))
                else:
                    for mkoma in char_cands:
                        UkeOpeList.append(Shogi_Operation(snd,True,mkoma,False,None,cell))
                    if kikikoma != shogi.Gyoku:
                        mudaAiCands.append(Shogi_Operation(snd,False,kikikoma.char,False,kikikoma.pos,cell))
                        if kikikoma.pos[1]>5 or cell[1]>5: #成って移動合い
                            mudaAiCands.append(Shogi_Operation(snd,False,kikikoma.char,True,kikikoma.pos,cell))

            else: #玉方の効きは２つ以上あるとき、移動合いは正当手
                for koma in rchsnd:
                    if koma != shogi.Gyoku:
                        idoUkeOpeList.append(Shogi_Operation(snd,False,koma.char,False,koma.pos,cell))
                        if koma.pos[1]>5 or cell[1]>5: #成って移動合い
                            idoUkeOpeList.append(Shogi_Operation(snd,False,koma.char,True,koma.pos,cell))
                for mkoma in char_cands:
                    UkeOpeList.append(Shogi_Operation(snd,True,mkoma,False,None,cell))

            if mudaAiCands:
                mudaAiCandsSet.append([cell,mudaAiCands])

        return UkeOpeList+idoUkeOpeList,mudaAiCandsSet
    
    def __isBlocking(self,shogi,koma):
        return shogi.isBlocking(koma)

    def dbgprint(self,txt):
        # print(txt)
        pass

    def HierPrintDic(self,fp=None):

        print(f"HierPrintDic: dic={self.dictop}")

        if self.dictop == {}:
            print('could not find sokution in ',self.MaxStep,'steps')
            print('Please check original problem or steps')
            return
        print('****Solution****')
        count=1
        dic = self.dictop
        next=dic['next']
        for i_ope in next:
            if i_ope in dic.keys():
                print('  *',dic[i_ope]['cnt'],i_ope,dic[i_ope]['success'])
                if fp:
                    print('  *',dic[i_ope]['cnt'],i_ope,dic[i_ope]['success'], file=fp)
                self.__subHierPrintDic(dic[i_ope],count,fp)
            
        return
    
    def __subHierPrintDic(self,dic,count,fp):

        count+=1
        
        next=dic['next']
        for i_ope in next:
            if i_ope in dic:
                print('    '*count,dic[i_ope]['cnt'],i_ope,dic[i_ope]['success'],f"empty:{dic[i_ope].get('empty',"-")}")
                if fp:
                    print('    '*count,dic[i_ope]['cnt'],i_ope,dic[i_ope]['success'],file=fp)
                self.__subHierPrintDic(dic[i_ope],count,fp)

        return

    # 回答ツリーから正解手順（最大手数・無知ゴマ使い切り、先手盤上駒数最小）を取得する
    def GetSolution2(self):
        if self.dictop == {}:
            print('could not find sokution in ',self.MaxStep,'steps')
            print('Please check original problem or steps')
            return False
        pass

        min_n_fst = 99

        #再帰的に解を探索する関数
        def rec_get_solution(dic, proc,count):
            nonlocal min_n_fst
            if not dic['next']:
                if count==self.depth:
                    if dic.get('empty',False):
                        if dic['n_fst']<min_n_fst:
                            min_n_fst = dic['n_fst']
                            self.solutions['answer'].insert(0,proc)
                        else:
                            self.solutions['answer'].append(proc)
                    else:
                        self.solutions['long'].append(proc)
                else:
                    self.solutions['short'].append(proc)
            for ope in dic['next']:
                proc_lst = proc+[ope]
                rec_get_solution(dic[ope],proc_lst,count+1)
            
            return

        self.solutions={'solutions':[],'answer':[],'long':[],'short':[]}
        dic = self.dictop
        next = dic['next']
        proc = [next[0]]

        #最初にdic階層のdepthを求める
        self.depth=0
        for i_ope in next:
            self.__subSearchDepth(dic[i_ope],1)

        print('GetSolution__subSerachDepth depth=',self.depth)
        
        # 再帰的に解を求める。breakなしで最後まで探索する。
        rec_get_solution(dic[next[0]],proc,1)

        self.solutions['solutions']= self.solutions['answer']+self.solutions['long']+self.solutions['short']

        # print('TsumeSolver3.GetSolution2:')
        # print(self.solutions['solutions'])

        return self.solutions['solutions'][0]

    def __subSearchDepth(self,dic,count):
        if count>self.depth:
            self.depth=count

        for i_ope in dic['next']:
            self.__subSearchDepth(dic[i_ope],count+1)

    # dicのコピーをするためにdeepcopyでは遅いので、必要最低限の専用コピーメソッドを作った。
    def copy_dic(self, dic:dict):
        retdic = dic.copy()

        for ope in dic['next']:
            retdic[ope]=self.copy_dic(dic[ope])
        
        return retdic

 

    
