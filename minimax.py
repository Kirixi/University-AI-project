# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
import random, time, util
from game import Directions,Agent
import game
from capture import noisyDistance
from myTeam import MonteCarloAgentDefense
from operator import itemgetter


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'DefensiveMinimaxAgent', second = 'MonteCarloAgentDefense'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class DummyAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)
    self.opponents = self.getOpponents(gameState)

    '''
    Your initialization code goes here, if you need any.
    '''


  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    '''
    You should change this in your own agent.
    '''

    return random.choice(actions)

class DefensiveMinimaxAgent(CaptureAgent):
    """
    This class provides some common elements to all of your
    multi-agent searchers.  Any methods defined here will be available
    to the MinimaxPacmanAgent, AlphaBetaPacmanAgent & ExpectimaxPacmanAgent.
    You *do not* need to make any changes here, but you can if you want to
    add functionality to all your adversarial search agents.  Please do not
    remove anything, however.
    Note: this is an abstract class: one that should not be instantiated.  It's
    only partially specified, and designed to be extended.  Agent (game.py)
    is another abstract class.
    """
    def registerInitialState(self, gameState):
        
        CaptureAgent.registerInitialState(self, gameState)
        self.opponents = self.getOpponents(gameState)
        self.beliefsCounter = util.Counter()
        opponents = self.getOpponents(gameState)
        self.legalPositions = self.getAllLegalPositions(gameState)
        self.initialAgentPos = gameState.getInitialAgentPosition(self.index)
        self.opponent_jail_pos = [gameState.getInitialAgentPosition(opponents[i]) for i in range(len(opponents))]
        xOpp, YOpp = min(self.opponent_jail_pos)
        xInit, YInit = self.initialAgentPos
        
        self.mid = abs(xOpp - xInit)

    


  
    def getAllLegalPositions(self, gameState):
        walls = gameState.getWalls()
        legalPositions = []
        for l in walls:
            row = [not a for a in l]
            legalPositions.append(row)

        legalPositions_list = []
        for x in range(len(legalPositions)):
            for y in range(len(legalPositions[x])):
                position = (x, y)
                if legalPositions[x][y]:
                    legalPositions_list.append(position)
        return legalPositions_list
    
    def isInHomeTerritory(self, pos):
        x, y = pos
        x1, y1 = self.initialAgentPos
        return self.mid > abs(x - x1)

    def chooseAction(self, gameState):
        self.agents = [self.index]
        for opponents in self.getOpponents(gameState):
            if gameState.getAgentPosition(opponents):
                self.agents.append(opponents)

        state = gameState.getAgentState(self.index)
        danger = not state.isPacman and state.scaredTimer > 0
        if danger:
            self.turns = len(self.agents)  
            agent_turn = 0
            agentIndex = self.agents[agent_turn]
            return self.AlphaBetaAgent(gameState, 1, agentIndex, agent_turn)

        return self.ghost_Action(gameState)

    def ghost_Action(self, gameState):
        own_territory = util.Counter()
        for opponent in self.opponents:
            b = self.beliefsCounter[opponent]
            for position in self.legalPositions:
                if self.isInHomeTerritory(position):
                    own_territory[position] += b[position]

        own_territory.normalize()
        actions = gameState.getLegalActions(self.index)
        dist_to_ghost = []

        for action in actions:
            successorState = gameState.generateSuccessor(self.index, action)
            state = successorState.getAgentState(self.index)
            new_agentpos = state.getPosition()
            distance_to_ghost = self.distancer.getDistance(new_agentpos, own_territory.argMax())
            if not state.isPacman:
                dist_to_ghost.append((action, distance_to_ghost))
        return min(dist_to_ghost, key=itemgetter(1))[0]
    
    def evaluationFunction(self, gameState):
        opponents = self.getOpponents(gameState)
        total_distance = 0
        for opponent_Index in opponents:
            opponent_state = gameState.getAgentState(opponent_Index)
            opponent_pos = opponent_state.getPosition()
            if opponent_pos:
                distance = noisyDistance(gameState.getAgentState(self.index).getPosition(), opponent_pos)
                total_distance += distance

        return -total_distance

class minimaxAgent():
    def getAction(self, gameState):
        """
        Returns the minimax action from the current gameState using self.depth
        and self.evaluationFunction.
        Here are some method calls that might be useful when implementing minimax.
        gameState.getLegalActions(agentIndex):
        Returns a list of legal actions for an agent
        agentIndex=0 means Pacman, ghosts are >= 1
        gameState.generateSuccessor(agentIndex, action):
        Returns the successor game state after an agent takes an action
        gameState.getNumAgents():
        Returns the total number of agents in the game
        gameState.isWin():
        Returns whether or not the game state is a winning state
        gameState.isLose():
        Returns whether or not the game state is a losing state
        """
        "*** YOUR CODE HERE ***"
        #function for max value
        self.agents=[self.index]
        agent_turn=0
        
        def maxValue(gameState,agentIndex,agent_turn,depth,alpha,beta):
            if depth>self.depth:
                return self.evaluationFunction(gameState)
            value=float('-inf')
            actions=gameState.getLegalActions(agentIndex)
            for act in actions:
                nextAgent=self.agents[agent_turn+1]
                value=max((value,self.minValue(gameState.generateSuccessor(agentIndex, act), depth, nextAgent, agent_turn + 1,
                                      alpha, beta)))
           
        #function for minimum value
        def minValue(gameState,agentIndex,agent_turn,depth,alpha,beta):
            if depth>self.depth:
                return self.evaluationFunction(gameState)
            value=float('inf')
            actions=gameState.getLegalActions(agentIndex)
            if  agent_turn== self.turns - 1:
                next_turn=0
                nextAgent = self.agents[next_turn]  # whose turn it is next
                for act in actions:
                    value = min(value,
                        self.maxValue(gameState.generateSuccessor(agentIndex, act), depth + 1, nextAgent, next_turn,
                                      alpha, beta))
                    if value < alpha:
                        return value
                    beta = min(beta, value)
                return value

            for act in actions:
                nextAgent = self.agents[agent_turn + 1]
                value = min((value, self.minValue(gameState.generateSuccessor(agentIndex, act), depth, nextAgent, agent_turn + 1,
                                      alpha, beta)))
                if value < alpha:
                    return value
                beta = min(beta, value)
            return value

    def AlphaBetaAgent(self,gameState,depth,agentIndex,agent_turn):
        """
        Your minimax agent with alpha-beta pruning 
        """

        alpha = float("-inf")
        beta = float("inf")
        value = float("-inf")
        actions = gameState.getLegalActions(agentIndex)
        previous_value= float("-inf")  
        best_Action = Directions.STOP
        for act in actions:
            if agent_turn < len(self.agents) - 1:
                nextAgent = self.agents[agent_turn + 1]  
                value = max(value,
                        self.minValue(gameState.generateSuccessor(agentIndex, act), depth, nextAgent, agent_turn + 1,
                                      alpha, beta))
                if value > previous_value:
                    best_Action = act
                if value >= beta:
                    previous_value= value
        return best_Action 