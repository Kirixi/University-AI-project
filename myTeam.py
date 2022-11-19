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


from itertools import count
from platform import node
from unittest import result
from captureAgents import CaptureAgent
import random, time, util
from game import Directions, Actions
import game
import math
import time

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'MasterAStarAgent', second = 'MonteCarloAgentDefense', numTraining = 0):
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


class MonteCarloAgentDefense(CaptureAgent):

  
  
  def registerInitialState(self, gameState):
    walls = list(gameState.getWalls())
    walls_width = len(walls)
    midpoint = int((walls_width/2))
    self.start = gameState.getAgentPosition(self.index)
    self.enemyPos = None
    self.numFoodToEat = len(self.getFood(gameState).asList())
    self.numFoodToDefend = len(self.getFoodYouAreDefending(gameState).asList())
    self.foodEatenAt = self.start
    self.previousDistance = 0
    self.lastKnownPos = self.start
    self.enemyPacmanEntered = False
    self.AStarAttackAgent = OffensiveAStarAgent(self.index)
    self.AStarAttackAgent.registerInitialState(gameState)
    if gameState.isOnRedTeam(self.index):
      self.enemiesIndices = gameState.getBlueTeamIndices()
    else:
      self.enemiesIndices = gameState.getRedTeamIndices()
    self.enemyIndices = []
    self.barPos = 0
    if gameState.isOnRedTeam(self.index):
      midpoint = int((walls_width/2))-1
    self.barrier = []
    for i, row in enumerate(walls[midpoint]):
        if row is False:
            self.barrier.append((int(midpoint), int(i)))
      
      
    CaptureAgent.registerInitialState(self, gameState)
  
  #Chooses particular action
  def chooseAction(self, gameState):
    self.enemyPacmanEntered = False
    for enemyIndex in self.enemiesIndices:
      if gameState.getAgentState(enemyIndex).isPacman:
        self.enemyPacmanEntered = True
        break
    depth=2
    action=self.MonteCarloTreeSearch(gameState,depth,self)
    # action = self.AStarAttackAgent.chooseAction(gameState)
    # if self.enemyPacmanEntered:
    #   depth=2
    #   action=self.MonteCarloTreeSearch(gameState,depth,self)
    
    
    if action==None:
      #if there are no actions select any random action or continue calling actions of monte carlo
      action=random.choice(gameState.getLegalActions(self.index))

    return action
  
  #to select a node
  def select(self,node):
    # node is tree from the monte carlo node referred to as root node
    if node.successorNode==[]:
      return node
    
    currNode=node
    c=0
    while currNode.successorNode!=[] and c!=len(currNode.successorNode):
      for i, s in enumerate(currNode.successorNode):
        if i not in currNode.v:
          # each time when the current node is not in list of visited node, 
          # append node to the list and select successor node as new current node 
          currNode.v.append(i)
          currNode=s
          c=0
          break
        c+=1
    return currNode

  # expanding a node
  def expand(self,leafNode):
    actions=leafNode.gameState.getLegalActions(leafNode.agent.index)
    if Directions.STOP in actions:
      actions.remove(Directions.STOP)
    #generate successor to the leaf node, get the actions and make the leaf node as parent node
    #append the successor node to the list
    for action in actions:
      node =MonteCarloNode(leafNode.gameState.generateSuccessor(leafNode.agent.index,action),
                              leafNode.agent,parentNode=leafNode,action=action)
      leafNode.successorNode.append(node)
    return leafNode

  #to simulate the expanded nodes  
  def simulate(self,childNode):
    #using the idea of minimax
    #update the score of node and return the best score out of the child nodes
    #evaluation function to evaluate the nodes

    if childNode.gameState.isOnRedTeam(childNode.agent.index):
      enemyIndices=childNode.gameState.getBlueTeamIndices()
    else:
      enemyIndices=childNode.gameState.getRedTeamIndices()

    def evaluationFunction(gameState,agentIndex,agent):
      # time.sleep(0.5)
      defenderPosition = gameState.getAgentState(agentIndex).getPosition()
      defFoodList = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()


      if gameState.isOnRedTeam(agentIndex):
                food = gameState.getRedFood().asList()
      else:
                food = gameState.getBlueFood().asList()

      #if the enemy is in blue teams territory then chase the pcman else chase the food
      #if red pacman is in own territory than patrol around the food else chase the opponent pacman

      enemyEnter = False
      distToEnemy = 999999
      for enemyIndex in self.enemiesIndices:

        if gameState.getAgentState(enemyIndex).isPacman: #check if the invaders are in home territory 
          if defenderPosition == self.enemyPos:
            return 1
          enemyEnter = True
          enemyPos = gameState.getAgentState(enemyIndex).getPosition()

          if enemyPos is not None:
            self.enemyPos = enemyPos
            distance = agent.getMazeDistance(defenderPosition, enemyPos)
            if distance < distToEnemy:
              distToEnemy = distance

            # if distance < distToEnemy:
            #   distToEnemy = distance

          else: # pos of last food eaten 
            defFoodList = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()
            foodEaten = []

            if self.getPreviousObservation() != None:
              prevFoodList = self.getFoodYouAreDefending(self.getPreviousObservation()).asList()
              foodEaten = list(set(defFoodList).symmetric_difference(set(prevFoodList)))

              if foodEaten != []:
                distanceToFood = [self.getMazeDistance(defenderPosition, foodCoord) for foodCoord in foodEaten]
                minDistance = min(distanceToFood)
                minIndex = distanceToFood.index(minDistance)
                self.foodEatenAt = foodEaten[minIndex]

              if len(defFoodList) < self.numFoodToDefend:
                distance = agent.getMazeDistance(defenderPosition, self.foodEatenAt)
                distToEnemy = distance

            return distToEnemy
            
        
      if enemyEnter:
        # print("Enemy distance: " + str(distToEnemy))
        return distToEnemy
      
      # if alliedTeamPosition != self.barrier[self.barPos]:
      #   # print(self.barPos)
      #   distanceToBar = agent.getMazeDistance(alliedTeamPosition,self.barrier[self.barPos])
      # else:
      #   self.barPos = (self.barPos + 1) % len(self.barrier)
      #   # print(self.barPos)
      #   distanceToBar = agent.getMazeDistance(alliedTeamPosition,self.barrier[self.barPos])

      if defenderPosition == self.enemyPos:
        self.enemyPos = 0
        return 1
      
      # if len(defFoodList) < 10:
      #   distToFood = 99999
      #   for nearest in defFoodList:
      #     distance = agent.getMazeDistance(defenderPosition,nearest)
      #     if distance < distToFood:
      #       distToFood=distance
      #   print("here")
      #   return distToFood
      
      distBarrierToFood = {}
      distanceToBar = 99999
      # defFoodList = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()
    
      for foodCoord in defFoodList:
        minDistBarrierToFood = min([self.getMazeDistance(foodCoord, coord) for coord in self.barrier])
        distBarrierToFood.update({foodCoord:minDistBarrierToFood})
    
      sortedDistBarrierToFood = list(dict(sorted(distBarrierToFood.items(), key=lambda item: item[1])))
      tenClosestFood = sortedDistBarrierToFood[0:10]
      
      if self.barPos >= len(tenClosestFood):
        self.barPos = len(tenClosestFood)-1
      
      if defenderPosition != tenClosestFood[self.barPos]:
        distanceToBar = agent.getMazeDistance(defenderPosition,tenClosestFood[self.barPos])
        if distanceToBar <= 1:
          return 1
      else:
        self.barPos = (self.barPos + 1) % len(tenClosestFood)
        # print(self.barPos)
        distanceToBar = agent.getMazeDistance(defenderPosition,tenClosestFood[self.barPos])

      totalDistance =  distanceToBar
      # print("total distance: " + str(totalDistance))
      
      return totalDistance

    #max value function for simulation
    def maxValue(gameState,agentIndex,agent,depth,enemies):
      # print("MaxValue Defend")
      if not gameState.getLegalActions(agent) or depth==childNode.depth:
        return [evaluationFunction(gameState,agentIndex,agent),None],False

    #min value function for simulation
    def minValue(gameState,agentIndex,agent,depth,enemies):
      if not gameState.getLegalActions(agentIndex) or depth==childNode.depth:
        # print("MinValue Defend")
        return [evaluationFunction(gameState,agentIndex,agent),None],True

    def minimaxSearch(gameState, agentIndex, agent, depth, enemies):
          return minValue(gameState, agentIndex, agent, depth, enemies)

    result =  minimaxSearch(childNode.gameState, childNode.agent.index, childNode.agent, 2, enemyIndices)[0][0]
    childNode.val = result

    return childNode.val



  #to backpropagate or rollback  
  def backPropogate(self, result, childNode):
        currNode = childNode
        temp = currNode.parentNode

        # print(currNode.action)
        
        for bestNode in childNode.successorNode:
          # print("best node value: ",bestNode.val)
          # print("best node action: ", bestNode.action)
        
          
          if bestNode.val == result:
            currNode = bestNode
            temp = currNode.parentNode
            break

        while temp is not None:
            if temp.val is None:
                temp.val = result
                currNode = temp
                temp = currNode.parentNode
            elif temp.val <= result:
                break
            else:
                temp.val = result
                currNode = temp
                temp = currNode.parentNode
        
        return currNode.action

  #tree search to perform the actions select,expand,simulate and backpropagate
  def MonteCarloTreeSearch(self,gameState,depth,agent):
    # create tree of gamestate and agent of monte carlo node
    tree = MonteCarloNode(gameState,agent)
    nodeCount = 0
    result=None

    leafNode=self.select(tree)
    # print(" select fuction")
    childNode=self.expand(leafNode)  
    # print(" expand fuction")
    for child in childNode.successorNode:
      nodeCount+=1
      if result is None:
        result=self.simulate(child)
        # print(" simulate fuction")
      else:
        # print(" simulate fuction else")
        temp=self.simulate(child)
        if result>temp:
          result=temp
    action=self.backPropogate(result,childNode)
    # print("action : " , action)
    # bestScore=9999999
    # for node in tree.successorNode:
    #   if node.val<=tree.val:
    #     action=node.action
    # print("action return : " , action)
    return action


    
#class to initialize or define a node
class MonteCarloNode:
  def __init__(self, gameState,agent,parentNode=None,val=0,action=None) :
    self.gameState = gameState
    self.agent = agent
    self.index=0
    self.parentNode=parentNode
    self.successorNode = [] # all the possible actions 
    self.visited = 0
    self.v = []
    self.val=val
    self.depth = 2
    self.action=action
    

# Monte carlo for Attack
def getMapAlleys(legalPos, gameState):
    Alleys = []
    #print(legalPos)
    while len(Alleys) != len(identifyAlleys(legalPos, Alleys, gameState)):
        Alleys = identifyAlleys(legalPos, Alleys, gameState)
    #print(mapAlleys)
    mapAlleys = Alleys
    return mapAlleys


def identifyAlleys(legalPos, alleys, gameState):
    alleysFound = alleys
    for pos in legalPos:
        nextAlleysLen = 0
        x, y = pos
        if (x, y + 1) in alleys:
          nextAlleysLen = nextAlleysLen + 1
        if (x, y - 1) in alleys:
          nextAlleysLen = nextAlleysLen + 1
        if (x + 1, y) in alleys:
          nextAlleysLen = nextAlleysLen + 1
        if (x - 1, y) in alleys:
          nextAlleysLen = nextAlleysLen + 1
        currAlley = len(Actions.getLegalNeighbors(pos, gameState.getWalls())) - 1 
        if pos not in alleys and currAlley - nextAlleysLen == 1:
            alleysFound.append(pos)
    return alleysFound



class MonteCarloAgentAttack(CaptureAgent):

  def registerInitialState(self, gameState):
    walls = list(gameState.getWalls())
    walls_width = len(walls)
    midpoint = int((walls_width/2))
    self.start = gameState.getAgentPosition(self.index)
    self.nearestFood = 0
    self.stuck = 0
    self.stuckFlag = False
    self.numFoodToEat = len(self.getFood(gameState).asList())
    self.numFoodToDefend = len(self.getFoodYouAreDefending(gameState).asList())
    self.foodEatenAt = self.start
    self.previousDistance = 0
    self.lastKnownPos = self.start
    self.MonteCarloAgentDefense = MonteCarloAgentDefense(self.index)
    self.MonteCarloAgentDefense.registerInitialState(gameState)
    self.defendTerritory = False
    if gameState.isOnRedTeam(self.index):
      self.enemiesIndices = gameState.getBlueTeamIndices()
    else:
      self.enemiesIndices = gameState.getRedTeamIndices()
    self.enemyIndices = []
    self.barPos = 0
    if gameState.isOnRedTeam(self.index):
      midpoint = int((walls_width/2))-1
    self.barrier = []
    for i, row in enumerate(walls[midpoint]):
        if row is False:
            self.barrier.append((int(midpoint), int(i)))
      
      
    CaptureAgent.registerInitialState(self, gameState)
  
  #Chooses particular action
  def chooseAction(self, gameState):
    self.defendTerritory = False
    friendly = [gameState.getAgentState(i) for i in self.getTeam(gameState) if i != self.index]
    numAttackers = 0
    for enemyIndex in self.enemiesIndices:
      if gameState.getAgentState(enemyIndex).isPacman:
        numAttackers += 1
      if gameState.getAgentState(enemyIndex).isPacman and friendly[0].isPacman and not gameState.getAgentState(self.index).isPacman:
        self.defendTerritory = True
        break
    
    if numAttackers > 0:
      self.defendTerritory = True
    
    depth=2
    action=self.MonteCarloTreeSearch(gameState,depth,self)
    if self.defendTerritory:
      self.MonteCarloAgentDefense.observationHistory = self.observationHistory
      action=self.MonteCarloAgentDefense.MonteCarloTreeSearch(gameState,depth,self)
      
   
    if action==None:
      #if there are no actions select any random action or continue calling actions of monte carlo
      action=random.choice(gameState.getLegalActions(self.index))

    return action
  
  #to select a node
  def select(self,node):
    # node is tree from the monte carlo node referred to as root node
    if node.successorNode==[]:
      return node
    
    currNode=node
    c=0
    while currNode.successorNode!=[] and c!=len(currNode.successorNode):
      for i, s in enumerate(currNode.successorNode):
        if i not in currNode.v:
          # each time when the current node is not in list of visited node, 
          # append node to the list and select successor node as new current node 
          currNode.v.append(i)
          currNode=s
          c=0
          break
        c+=1
    return currNode

  # expanding a node
  def expand(self,leafNode):
    actions=leafNode.gameState.getLegalActions(leafNode.agent.index)
    if Directions.STOP in actions:
      actions.remove(Directions.STOP)
    
    #generate successor to the leaf node, get the actions and make the leaf node as parent node
    #append the successor node to the list
    for action in actions:
      node =MonteCarloNode(leafNode.gameState.generateSuccessor(leafNode.agent.index,action),
                              leafNode.agent,parentNode=leafNode,action=action)
      leafNode.successorNode.append(node)
    return leafNode

  #to simulate the expanded nodes  
  def simulate(self,childNode):
    #evaluation function to evaluate the nodes

    if childNode.gameState.isOnRedTeam(childNode.agent.index):
      enemyIndices=childNode.gameState.getBlueTeamIndices()
    else:
      enemyIndices=childNode.gameState.getRedTeamIndices()

    def evaluationFunction(gameState,agentIndex,agent):

      # agentState = gameState.getAgentState(self.index)
      enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
      ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None]
      
      foods = self.getFood(gameState).asList()
      avoidGhost = False
      attackerPosition = gameState.getAgentState(agentIndex).getPosition()

      for ghost in ghosts:
        if agent.getMazeDistance(attackerPosition,ghost.getPosition()) < 5:
          avoidGhost = True
     
     
      distToFood = 999999
      if self.nearestFood == 0:
        for cords in foods:
          distance = agent.getMazeDistance(attackerPosition,cords)
          if distance < distToFood:
            distToFood = distance
            self.nearestFood = cords

      


      if avoidGhost:
        if self.stuckFlag: 
          if attackerPosition != self.nearestFood:
            self.stuckFlag = False
          distance = agent.getMazeDistance(attackerPosition,self.nearestFood)
          return distance 
        if attackerPosition in self.barrier:
          self.stuck += 1
        if self.stuck > 4:
          distanceToBarrier = [self.getMazeDistance(attackerPosition, coord) for coord in self.barrier]
          minDistance = max(distanceToBarrier)
          minIndex = distanceToBarrier.index(minDistance)
          self.nearestFood = self.barrier[minIndex]
          self.stuck = 0
          self.stuckFlag = True
          
        else:
          distanceToBarrier = [self.getMazeDistance(attackerPosition, coord) for coord in self.barrier]
          minDistance = min(distanceToBarrier)
          return minDistance

#

    #if the target is 1 step away from, return a distance of 1 to tell it to take the right action 
      if agent.getMazeDistance(attackerPosition,self.nearestFood) <= 1:
        for cords in foods:
          distance = agent.getMazeDistance(attackerPosition,cords)
          if distance < distToFood:
            distToFood = distance
            self.nearestFood = cords
        return 1

      if gameState.getAgentState(agentIndex).numCarrying < self.numFoodToEat and len(foods) > 2 and not avoidGhost:
        if attackerPosition != self.nearestFood:
          distance = agent.getMazeDistance(attackerPosition,self.nearestFood)
          return distance 
      else:
          distanceToBarrier = [self.getMazeDistance(attackerPosition, coord) for coord in self.barrier]
          minDistance = min(distanceToBarrier)
          return minDistance

      
      


    #min value function for simulation
    def minValue(gameState,agentIndex,agent,depth,enemies):

      if not gameState.getLegalActions(agentIndex) or depth==childNode.depth:
        # print("minValue")
        return [evaluationFunction(gameState,agentIndex,agent),None],True

      
    def minimaxSearch(gameState, agentIndex, agent, depth, enemies):
          return minValue(gameState, agentIndex, agent, depth, enemies)

    result =  minimaxSearch(childNode.gameState, childNode.agent.index, childNode.agent, 2, enemyIndices)[0][0]
    childNode.val = result

    return childNode.val



  #to backpropagate or rollback  
  def backPropogate(self, result, childNode):
        currNode = childNode
        temp = currNode.parentNode

        # print(currNode.action)
        
        for bestNode in childNode.successorNode:
          # print("best node value: ",bestNode.val)
          # print("best node action: ", bestNode.action)
          
          if bestNode.val == result:
            currNode = bestNode
            temp = currNode.parentNode
            break

        while temp is not None:
            if temp.val is None:
                temp.val = result
                currNode = temp
                temp = currNode.parentNode
            elif temp.val <= result:
                break
            else:
                temp.val = result
                currNode = temp
                temp = currNode.parentNode
        
        # print("action in propagate: ", currNode.action)
        # print()
        return currNode.action

  #tree search to perform the actions select,expand,simulate and backpropagate
  def MonteCarloTreeSearch(self,gameState,depth,agent):
    tree = MonteCarloNode(gameState,agent)
    result=None
    leafNode=self.select(tree)
    # print(" select fuction")
    childNode=self.expand(leafNode)  

    # print(" expand fuction")
    for child in childNode.successorNode:
      if result is None:
        result=self.simulate(child)
        # print(" simulate fuction")
      else:
        # print(" simulate fuction else")
        temp=self.simulate(child)
        if result>temp:
          result=temp


    action = self.backPropogate(result,childNode)
    # print("action", action)
    # for node in tree.successorNode:
    #   print(tree.val)
    #   if node.val <= tree.val:
    #     action = node.action
    # print("action", action)
    return action

def findDistance(pos1, pos2):
  x1, y1 = pos1
  x2, y2 = pos2
  d = (x1-x2)**2 + (y1-y2)**2
  return int(math.sqrt(d))


global carry_limit

class MasterAStarAgent(CaptureAgent):
  
  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    self.AStarAttackAgent = OffensiveAStarAgent(self.index)
    self.AStarAttackAgent.registerInitialState(gameState)
    self.AStarDefendAgent = DefensiveAStarAgent(self.index)
    self.AStarDefendAgent.registerInitialState(gameState)
    self.MonteCarloDefense = MonteCarloAgentDefense(self.index)
    self.MonteCarloDefense.registerInitialState(gameState)
    self.numFoodToEat = len(self.getFood(gameState).asList())
    self.targetNumFood = 2
    self.AStarDefendAgent.numFoodToEat = self.targetNumFood
    self.enemyPacmanEntered = False
    if gameState.isOnRedTeam(self.index):
      self.enemiesIndices = gameState.getBlueTeamIndices()
    else:
      self.enemiesIndices = gameState.getRedTeamIndices()
    self.enemyIndices = []
    CaptureAgent.registerInitialState(self, gameState)

  def chooseAction(self, gameState):
    self.AStarAttackAgent.observationHistory = self.observationHistory
    self.AStarDefendAgent.observationHistory = self.observationHistory
    self.MonteCarloDefense.observationHistory = self.observationHistory
    
    self.enemyPacmanEntered = False
    for enemyIndex in self.enemiesIndices:
      if gameState.getAgentState(enemyIndex).isPacman:
        self.enemyPacmanEntered = True
        break
    
    
    
    agentState = gameState.getAgentState(self.index)
    if self.getScore(gameState) < self.targetNumFood:
      return self.AStarAttackAgent.chooseAction(gameState)
    else:
      self.enemyPacmanEntered = False
      for enemyIndex in self.enemiesIndices:
        if gameState.getAgentState(enemyIndex).isPacman:
          self.enemyPacmanEntered = True
          break
      
      if self.enemyPacmanEntered:
        depth=2
        return self.MonteCarloDefense.chooseAction(gameState)
      return self.AStarDefendAgent.chooseAction(gameState)








class AStarAgent(MasterAStarAgent):
  """
  A base class for AStarSearch agents that chooses actions using heaursitics
  """

  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    self.numFoodToEat = len(self.getFood(gameState).asList())
    self.legalActions = [pos for pos in gameState.getWalls().asList(False)]
    self.alleys = getMapAlleys(self.legalActions, gameState)
    self.safePositions = list(set(self.legalActions) - set(self.alleys))
    self.numFoodToDefend = len(self.getFoodYouAreDefending(gameState).asList())
    self.foodEatenAt = self.start
    self.defendFoodIndex = 0
    self.visited = []
    self.enemyPacman = self.start
    
    # self.AStarAttackAgent = OffensiveAStarAgent(self.index)
    # self.AStarAttackAgent.registerInitialState(gameState)
    # self.AStarDefendAgent = DefensiveAStarAgent(self.index)
    # self.AStarDefendAgent.registerInitialState(gameState)
    
    #Find the coordinates of barrier that seperates blue from red team
    
    walls = list(gameState.getWalls())
    self.walls_width = len(walls)
    self.midpoint = int((self.walls_width/2))
    
    if gameState.isOnRedTeam(self.index):
      self.midpoint = int((self.walls_width/2))-1
    self.barrier = []
    for i, row in enumerate(walls[self.midpoint]):
        if row is False:
            self.barrier.append((int(self.midpoint), int(i)))
      
    self.defendFoodAt = self.barrier[0]
    self.count = True
    CaptureAgent.registerInitialState(self, gameState)
   
  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    pos = gameState.getAgentState(self.index).getPosition()
    x, y = int(pos[0]), int(pos[1])
    # if (x,y) == self.defendFoodAt:
    #   self.visited.append((x,y))
    
    if self.defendFoodIndex == 0:
      self.count = True
    elif self.defendFoodIndex == len(self.barrier) - 1:
      self.count = False
    
    if self.defendFoodAt == (x,y) and (x,y) not in self.visited:
      if self.count:
        self.defendFoodIndex += 1
      elif not self.count:
        self.defendFoodIndex -= 1
      self.visited.append((x,y))
    
    if self.defendFoodIndex == len(self.barrier)-1:
      self.visited = []
    elif self.defendFoodIndex == 0:
      self.visited = []
    
    
    # if self.getScore(gameState) < 0:
    #   actions = self.AStarAttackAgent.chooseAction(gameState)
    # else:
    #   actions = self.AStarDefendAgent.chooseAction(gameState)
    
    actions = self.AStarSearch(gameState)

    # print(gameState.getAgentDistances())
    '''
    You should change this in your own agent.
    '''
    if len(actions) == 0:
      return 'Stop'
    else:
      return actions[0]
  
  def AStarSearch(self, gameState):
    foodList = self.getFood(gameState).asList()
    foodInAlley = set(self.alleys).intersection(self.getFood(gameState).asList())
    safeFood = list(set(foodList) - foodInAlley)
    capsules = self.getCapsules(gameState)
    score = self.getScore(gameState)
    # if safeFood:
    #   foodList = safeFood
   
    # print(len(foodToEat))
    # print(len(safeFood))
    agentState = gameState.getAgentState(self.index)
    frontier = util.PriorityQueue()
    actions = []
    position = gameState.getAgentPosition(self.index)
    cost = self.heauristic(foodList, position, agentState, gameState)
    explored = {}
    explored.update({position:cost})
    initialState = (position, actions, gameState, cost)
    frontier.push(initialState, cost)
    

    while(not frontier.isEmpty()):
      currentPos, actions, currGameState, cost = frontier.pop()
      
      if self.isGoalState(currGameState, foodList, agentState, safeFood, capsules, score):
        return actions
      
      for successor in self.getSuccessors(currGameState):
        pos, action, state = successor
        totalCost = cost + self.heauristic(foodList, pos, agentState, gameState)
        if pos not in explored:
          frontier.push((pos, actions + [action], state, totalCost), totalCost)
          explored.update({pos:totalCost})
        elif pos in explored and explored[pos] > totalCost:
          frontier.update((pos, actions + [action], state, totalCost), totalCost)
             
    return []
 
      
  def getSuccessors(self, gameState):
    pass
       
  def isGoalState(self, gameState, foodList, agentState):
    pass
  
  def heauristic(self, gameState, position):
    pass

class OffensiveAStarAgent(AStarAgent):
  
  def chooseAction(self, gameState):
    actions = self.AStarSearch(gameState)
    legalActions = list(gameState.getLegalActions(self.index))
    enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None]
    ghostsPos = [ghost.getPosition() for ghost in ghosts if ghost.scaredTimer == 0]
    
    foodList = self.getFood(gameState).asList()
    foodInAlley = set(self.alleys).intersection(self.getFood(gameState).asList())
    safeFood = list(set(foodList) - foodInAlley)
    safePositions = []
    capsules = self.getCapsules(gameState)
    if len(actions) == 0:
      for action in legalActions:
      
        if action != 'Stop':
          
          successor = gameState.generateSuccessor(self.index, action)
          pos = successor.getAgentState(self.index).getPosition()
          
          if pos in capsules:
            return action
          elif pos in safeFood:
            return action
          elif pos in self.safePositions and pos not in ghostsPos:
            legalActions.remove(action)
            safePositions.append(action)
          
          if len(safePositions) > 0:
            return random.choice(safePositions)
        
      else:
        return 'Stop'
    else:
      return actions[0]
  
  def getSuccessors(self, gameState):
    walls = gameState.getWalls()
    actions = gameState.getLegalActions(self.index)
    successors = []
    
    enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None]
    ghostsPos = [ghost.getPosition() for ghost in ghosts if ghost.scaredTimer == 0]
    
    food = self.getFood(gameState)
    
    for action in actions:
      if action != 'Stop':
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        x, y = int(pos[0]), int(pos[1])
        
        minDisToGhost = min([self.getMazeDistance(pos, ghost) for ghost in ghostsPos], default=999)
        
        if not(minDisToGhost > 0 and minDisToGhost < 2):
          successors.append((pos, action, successor))

    return successors
  
  def isGoalState(self, gameState, foodList, agentState, safeFood, capsules, score):
    
    walls = gameState.getWalls()
    pos = gameState.getAgentState(self.index).getPosition()
    x, y = int(pos[0]), int(pos[1])
    
    prevState = self.getPreviousObservation()
    px, py = self.start
    if prevState != None:
      prevPos = prevState.getAgentState(self.index).getPosition()
      px, py = int(prevPos[0]), int(prevPos[1])
    
    # pacmanStuck = False
    # if (x,y) == (px, py):
    #   pacmanStuck = True
    
    
    # print(capsules)
    
    
    enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None]
    ghostsPos = [ghost.getPosition() for ghost in ghosts if ghost.scaredTimer == 0]
    minDisToGhost = min([self.getMazeDistance(pos, ghost) for ghost in ghostsPos], default=999)
    avoidGhost = False
    scaredGhost = False
    
    for ghost in ghosts:
      if ghost.scaredTimer == 0:
        avoidGhost = True
      elif ghost.scaredTimer > 0:
        scaredGhost = True
   
    
    if agentState.numCarrying < (2-score) and len(foodList) > 2:
      if safeFood and avoidGhost:  
        distanceToFood = [self.getMazeDistance((x,y), food) for food in safeFood]
        minDistance = min(distanceToFood)
        minIndex = distanceToFood.index(minDistance)
        return safeFood[minIndex] == (x,y)
      
      elif avoidGhost and capsules and agentState.isPacman:
        # distanceToBarrier = [self.getMazeDistance((x,y), coord) for coord in self.barrier]
        # minDistance = min(distanceToBarrier)
        # minIndex = distanceToBarrier.index(minDistance)
        
        distanceToCapsule = [self.getMazeDistance((x,y), capsule) for capsule in capsules]
        minDistanceToCapsule = min(distanceToCapsule, default=999)
        minIndex = distanceToCapsule.index(minDistanceToCapsule)
        
        # distanceToSafety = [self.getMazeDistance((x,y), pos) for pos in self.safePositions]
        # maxdistanceToSafety = max(distanceToSafety)
        # maxIndex = distanceToSafety.index(maxdistanceToSafety)
        
        # # if minDistanceToCapsule < minDistance and capsules:
        # #   return capsules[distanceToCapsule.index(minDistanceToCapsule)] == (x,y)
        # rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        # possibleGhostPos = [Actions.getLegalNeighbors(pos, walls) for pos in ghostsPos]
        # myNbrs = Actions.getLegalNeighbors(pos, walls)
        # for ghost in possibleGhostPos:
        #   safePos = list(set(ghost) - set(myNbrs))
        #   for p in safePos:
        #     if p != pos and p not in ghostsPos and p in self.safePositions:
        #       return p == (x,y)
        
            
        return capsules[minIndex] == (x,y)
      elif scaredGhost and (minDisToGhost > 0 and minDisToGhost < 3):
        ghostsPos = [ghost.getPosition() for ghost in ghosts]
        disToGhost = [self.getMazeDistance(pos, ghost) for ghost in ghostsPos]
        minDistance = min(disToGhost)
        minIndex = disToGhost.index(minDistance)

        return ghostsPos[minIndex] == (x,y)
        
      else:
        distanceToFood = [self.getMazeDistance((x,y), food) for food in foodList]
        minDistance = min(distanceToFood)
        minIndex = distanceToFood.index(minDistance)
        
        return foodList[minIndex] == (x,y)
    
    else:
      distanceToBarrier = [self.getMazeDistance((x,y), coord) for coord in self.barrier]
      minDistance = min(distanceToBarrier)
      minIndex = distanceToBarrier.index(minDistance)
      
      return self.barrier[minIndex] == (x,y)
  
  def heauristic(self, foodList, position, agentState, gameState):
    minDistance = 0
    
    enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None]
    avoidGhost = False
    
    for ghost in ghosts:
      if ghost.scaredTimer < 3:
        avoidGhost = True
        
    prevState = self.getPreviousObservation()
    px, py = self.start
    if prevState != None:
      prevPos = prevState.getAgentState(self.index).getPosition()
      px, py = int(prevPos[0]), int(prevPos[1])
    
    # pacmanStuck = False
    # if position == (px, py):
    #   pacmanStuck = True
    
    if agentState.numCarrying < self.numFoodToEat and len(foodList) > 2:  
      minDistance = min([self.getMazeDistance(position, food) for food in foodList])
      
    # elif pacmanStuck:
    #   minDistance = self.getMazeDistance(position, self.start)
    else:
      minDistance = min([self.getMazeDistance(position, coord) for coord in self.barrier])
      
    return minDistance


class DefensiveAStarAgent(AStarAgent):
  def getSuccessors(self, gameState):
    walls = gameState.getWalls()
    actions = gameState.getLegalActions(self.index)
    successors = []
    
    enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None]
    ghostsPos = [ghost.getPosition() for ghost in ghosts if ghost.scaredTimer == 0]
    
    agent = gameState.getAgentState(self.index)
    food = self.getFood(gameState)
    
    for action in actions:
      if action != 'Stop':
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        x, y = int(pos[0]), int(pos[1])
        agent = successor.getAgentState(self.index)
        minDisToGhost = min([self.getMazeDistance(pos, ghost) for ghost in ghostsPos], default=999)
        if not agent.isPacman:
          successors.append((pos, action, successor))

    return successors
  
  def isGoalState(self, gameState, foodList, agentState, safeFood, capsules, score):
    pos = gameState.getAgentState(self.index).getPosition()
    x, y = int(pos[0]), int(pos[1])
    
    defFoodList = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()
    foodEaten = []
    
    enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    pacmans = [a for a in enemies if not a.isPacman and a.getPosition() != None]
    pacmanPos = [pacman.getPosition() for pacman in pacmans]
    eatPacman = False
    
    if pacmanPos != []:
      eatPacman = True
    
    
  
    if self.getPreviousObservation() != None:
      prevFoodList = self.getFoodYouAreDefending(self.getPreviousObservation()).asList()
      foodEaten = list(set(defFoodList).symmetric_difference(set(prevFoodList)))
      if foodEaten != []:
        self.foodEatenAt = foodEaten[0]
    
    if len(defFoodList) < self.numFoodToDefend and not eatPacman:
      return self.foodEatenAt == (x,y)
    
    elif eatPacman:
      if len(pacmanPos) == 2:
        distanceToPacman1 = [self.getMazeDistance(pacmanPos[0], barrier) for barrier in self.barrier]
        minDistance1 = min(distanceToPacman1)
        minIndex1 = distanceToPacman1.index(minDistance1)
        
        distanceToPacman2 = [self.getMazeDistance(pacmanPos[1], barrier) for barrier in self.barrier]
        minDistance2 = min(distanceToPacman2)
        minIndex2 = distanceToPacman2.index(minDistance2)
        
        if minDistance1 < minDistance2:
          self.enemyPacman = self.barrier[minIndex1]
          return self.barrier[minIndex1] == (x,y)
        else:
          self.enemyPacman = self.barrier[minIndex2]
          return self.barrier[minIndex2] == (x,y)
        
        
      distanceToPacman = [self.getMazeDistance(pacmanPos[0], barrier) for barrier in self.barrier]
      minDistance = min(distanceToPacman)
      minIndex = distanceToPacman.index(minDistance)
      self.enemyPacman = self.barrier[minIndex]
      return self.enemyPacman == (x,y)
      
    else:
      distBarrierToFood = {}
    
      for foodCoord in defFoodList:
        minDistBarrierToFood = min([self.getMazeDistance(foodCoord, coord) for coord in self.barrier])
        distBarrierToFood.update({foodCoord:minDistBarrierToFood})
    
      sortedDistBarrierToFood = list(dict(sorted(distBarrierToFood.items(), key=lambda item: item[1])))
      
      # if self.defendFoodIndex < len(sortedDistBarrierToFood):
      #   self.defendFoodAt = sortedDistBarrierToFood[self.defendFoodIndex]
      # print(self.def)
      self.defendFoodAt = self.barrier[self.defendFoodIndex]
      return self.defendFoodAt == (x,y)
      
    

  def heauristic(self, foodList, position, agentState, gameState):
    defFoodList = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()
    minDistance = 0
    if len(defFoodList) < self.numFoodToDefend:  
      minDistance = self.getMazeDistance(position, self.foodEatenAt)
    else:
      minDistance = self.getMazeDistance(position, self.defendFoodAt)
      
    return minDistance
  
  