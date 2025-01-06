import numpy as np
from typing import Optional,Literal,List,Tuple
import plotly.graph_objects as go

##################################################### Initializations ########################################

from math import comb

def Prob_bestOfK(K,p): ################ Util Function
    """
    p is the probability of winning a point.
    K is the number of games to be considered for 
    best of k
    """

    assert K % 2 != 0 , f" In best of k matches k must be odd, value passed is {K}"

    k = (K-1)//2

    sum = 0
    for i in range(1,k+2):
        sum += comb(K,k+i)*p**(k+i)*(1-p)**(k+1-i)
    
    return sum

# Probability curves for best of k families of games

FamilyBestKFig = go.Figure()

FamilyBestKFig.update_layout(
            height = 600,
            width = 600,
            xaxis = dict(
                title = 'Prob of P1 winning a point',
                range = [0,1]
            ),
            yaxis = dict(
                title = 'Prob of P1 winning the game scheme',
                range = [0,1]
            ),
        )

plow = 0.01
phigh = 0.99
pstep = 0.001
probs = np.arange(plow,phigh,pstep)

kvals = [ k for k in range(1,13,2)]
kvals += [ k for k in range(15,35,6)]
kvals += [ k for k in range(51,250,50)]

for k in kvals:
    FamilyBestKFig.add_trace(go.Scatter(x=probs, y= [Prob_bestOfK(k,p) for p in probs], mode='lines' , opacity=0.2, line=dict(color='grey'), name=f'Best of {k}', showlegend= False))


######################################################## Class for DCG ##################################### Directly competitive Games / Same Action Games

class HierarchyLevel:
    def __init__(self, childLevel : Optional[ "HierarchyLevel" ] = None , score : Optional[int] = None, winType : Literal['Target score','Best of score'] = 'Target score') -> None:
        """
        Creates a Hierarchy level object.

        score -> score required to win the level

        winType ->  * Target score (default) 
                    * Best of score 
        
        Note: TieBreakers : None      if Best of score is the winType
                            Deuce     if Target score is the winType
        
        you can set Tie Breakers using object.set_tieRules() methods. 

        childLevel -> lower level Hierarchy object (default : None)

        Note : if childLevel is None then the Hierarchy object is the lowest 
        Level in the game scheme hierarchy. The probability to win a point can 
        be set through this object using object.set_p() method.  
        """
        if childLevel == None:
            assert score == None, "Base level Object cannot have any score as it is the unit action of scoring a point in game scheme"

        self.__score = score
        self.__winType = winType
        self.child = childLevel


        self.__P1score = 0
        self.__P2score = 0
        self.__currScoreIter = 0
        self.Length = 0
        self.lvlHistory = dict()
        # self.FullHistory = dict()

        if self.child == None:
            self.lvl = 0
            self.__p = 0.6
        else:
            self.lvl = self.child.lvl + 1

            self.__tieRules = {                                                        # dict -> tiescore : (leadDiff,simChildlvl)
                self.__score-1 : (2,self.lvl-1)                                        # Deuce Rule
            }


################################ Private Methods ########

    def __checkContinuePlay(self,currScoreIter) -> bool:

        if self.__P1score + (self.__score - currScoreIter) < self.__P2score:            # can P1 catch upto P2
            return False
        if self.__P2score + (self.__score - currScoreIter) < self.__P1score:            # can P2 catch upto P1
            return False
        return True
    
        
    # generic deuce --> geuce ??
    def __tiebreaker(self,leadDiff,simChildlvl):

        assert leadDiff > 0, 'Difference in points / lead should be positive'
        assert simChildlvl < self.lvl, 'child level to be simulated should be less than the level of current object'

        child = self.getChildAt(simChildlvl)

        self.lvlHistory.update({'Tie':f'TieBreaker : get lead of {leadDiff}, on lvl -> {simChildlvl}'})
        self.__currScoreIter += 1

        P1 = 0
        P2 = 0

        diff = 0

        while diff != leadDiff:

            winner = child.Simulate()

            self.Length += child.Length
            self.lvlHistory.update( { f'D {self.__currScoreIter} L-> {simChildlvl}' : child.getLevelScore() } )

            if winner == 1:
                P1 += 1
                self.__P1score += 1 if self.lvl - simChildlvl == 1 else 0
            else:
                P2 += 1
                self.__P2score += 1 if self.lvl - simChildlvl == 1 else 0

            diff = abs(P1-P2)
            self.__currScoreIter += 1
        
        
        return 1 if P1 > P2 else 2

    
################################ Public Methods ######### 

    def getChildAt(self,lvl):
        """
        Returns HierarchyLevel child object at lvl (argument to the function)
        """
        if self.lvl == lvl:
            return self
        
        child = self.child
        while lvl != child.lvl:
            child = child.child
        
        return child
    
    def set_p(self,p):
        """
        provide probability of scoring a point in base level (p)  
        default value is set -> p = 0.6

        """
        assert self.lvl == 0 , "Not a base level object, this method is available only for base level object"
        self.__p = p

    def getLevelScore(self):
        """
        Returns the Score of the level (after simulation) 
        """
        if self.__P1score == 0 and self.__P2score == 0:
            return ' Not yet simulated'
        else:
            return f' {self.__P1score} - {self.__P2score} '
    
    def set_tieRules(self,tieRulesDict):
        """
        Provide a dictionary 

        { tiePts : (leadDiff,simChildlvl) }

        Here when the score of the level reaches tiePts,
        players will play simchildlvl -> some level in game scheme
        to get a lead of leadDiff in the score
        """
        self.__tieRules = tieRulesDict

    def Simulate(self) -> Literal[1,2] :
        """
        Simulates the Game Scheme defined by the user
        """

        self.__P1score = 0
        self.__P2score = 0

        if self.lvl == 0:
            self.Length = 0
            self.Length += 1
            if np.random.uniform(0,1) <= self.__p:
                self.__P1score += 1
                return 1
            else:
                self.__P2score += 1
                return 2
        else:
            LevelOver = False

            self.Length = 0
            self.lvlHistory = dict()
            self.__currScoreIter = 1

            while not LevelOver:
                winner = self.child.Simulate()

                self.lvlHistory.update({self.__currScoreIter:self.child.getLevelScore()})

                self.Length += self.child.Length

                if winner == 1:
                    self.__P1score += 1
                else:
                    self.__P2score += 1
                
                if self.__winType == 'Best of score':
                    if not self.__checkContinuePlay(self.__currScoreIter):
                        return 1 if self.__P1score > self.__P2score else 2
                    
                # check for tie rules
                if self.__winType == 'Target score':
                    inTieBreaker = False
                    Tiewinner = None
                    for tiescore,(leadDiff,simChildlvl) in self.__tieRules.items():
                        if (self.__P1score == self.__P2score) and (self.__P1score == tiescore):
                            Tiewinner = self.__tiebreaker(leadDiff,simChildlvl)
                            inTieBreaker = True
                    
                    if inTieBreaker == True:
                        return Tiewinner
                            
                    
                if self.__P1score == self.__score:
                    LevelOver = True
                    return 1
                elif self.__P2score == self.__score:
                    LevelOver = True
                    return 2 
                
                self.__currScoreIter += 1
    
    def ProbPlot(self,Numsim = 1000, plow = 0.2, phigh = 0.85, pstep = 0.05, ShowBestKFamily = False):
        
        if ShowBestKFamily:
            fig = go.Figure(FamilyBestKFig)
        else:
            fig = go.Figure()

            fig.update_layout(
                height = 600,
                width = 900,
                xaxis = dict(
                    title = 'Prob of P1 winning a point'
                ),
                yaxis = dict(
                    title = 'Prob of P1 winning the game scheme'
                ),
            )

        baseLvl = self.getChildAt(0)
        pwinArr = []
        probs = np.arange(plow,phigh,pstep)

        for p in probs:
            Pwin = 0
            baseLvl.set_p(p)
            for _ in range(Numsim):
                if self.Simulate() == 1:
                    Pwin += 1
            pwinArr.append(Pwin/Numsim)

        trace = go.Scatter(x=probs, y=pwinArr, mode='lines')
        fig.add_trace(trace)

        fig.show()

        return trace

    def ExpLenPlot(self,Numsim = 1000, plow = 0.2, phigh = 0.85, pstep = 0.05) -> go.Trace:
        
        fig = go.Figure()

        fig.update_layout(
            height = 600,
            width = 900,
            xaxis = dict(
                title = 'Prob of P1 winning a point'
            ),
            yaxis = dict(
                title = 'Expected Length of game scheme'
            ),
        )

        baseLvl = self.getChildAt(0)
        ELenArr = []
        probs = np.arange(plow,phigh,pstep)

        for p in probs:
            ExLen = 0
            baseLvl.set_p(p)
            for _ in range(Numsim):
                self.Simulate()
                ExLen += self.Length
            ELenArr.append(ExLen/Numsim)

        trace = go.Scatter(x=probs, y=ELenArr, mode='lines')
        fig.add_trace(trace)

        fig.show()

        return trace


###################################################################### Util Functions ##########################################################

def ComparePlots(Gameschemes : List[Tuple[HierarchyLevel,str]], NumSim = 2000, plow = 0.2, phigh = 0.85, pstep = 0.05, ShowBestKFamily = False) -> Tuple[go.Figure,go.Figure]:
    """
    Used to plot 
    * ( Prob. win game scheme vs. Prob. win point )
    * ( Expected Length of game scheme vs. Prob. win point )
    given a list of tuples (HierarchyLevel Object (game scheme),game scheme name) 
    in order to visually compare them
    """

    ################ Plotting ################

    Lfig = go.Figure()

    if ShowBestKFamily:
        Pfig = go.Figure(FamilyBestKFig)
    else:
        Pfig = go.Figure()

    Pfig.update_layout(
        height = 600,
        width = 900,
        xaxis = dict(
            title = 'Prob of P1 winning a point'
        ),
        yaxis = dict(
            title = 'Prob of P1 winning the game scheme'
        ),
    )

    Lfig.update_layout(
        height = 600,
        width = 900,
        xaxis = dict(
            title = 'Prob of P1 winning a point'
        ),
        yaxis = dict(
            title = 'Expected Length of game scheme'
        ),
    )

    ############## simulating schemes #######

    probs = np.arange(plow,phigh,pstep)

    pwinarr = dict()
    ExLenarr = dict()

    for scheme,schemeName in Gameschemes:

        print(f' Simulating Scheme {schemeName}')

        pwinarr.update({schemeName : []})
        ExLenarr.update({schemeName : []})

        baselvl = scheme.getChildAt(0)

        for p in probs:

            Exlen = 0
            pwin = 0
            baselvl.set_p(p)

            for _ in range(NumSim):
                winner = scheme.Simulate()
                Exlen += scheme.Length
                pwin += 1 if winner == 1 else 0
            
            pwinarr[schemeName].append(pwin/NumSim)
            ExLenarr[schemeName].append(Exlen/NumSim)
        
        Pfig.add_trace(go.Scatter(x=probs ,y=pwinarr[schemeName],mode='lines',name=schemeName))
        Lfig.add_trace(go.Scatter(x=probs ,y=ExLenarr[schemeName],mode='lines',name=schemeName))
    
    
    Pfig.show()
    Lfig.show()

    return Pfig,Lfig


########################################## Sequentially Competitive Games #########################################

    

    


    


