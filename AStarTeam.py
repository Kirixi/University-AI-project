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


from cmath import cos
from turtle import position
from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game
import util

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveAStarAgent', second = 'DefensiveAStarAgent', numTraining = 0):
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

class AStarAgent(CaptureAgent):
  """
  A base class for AStarSearch agents that chooses actions using heaursitics
  """

  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    self.numFoodToEat = len(self.getFood(gameState).asList())
    self.numFoodToDefend = len(self.getFoodYouAreDefending(gameState).asList())
    self.foodEatenAt = self.start
    self.numOfMoves = 0
    self.defendFoodIndex = 0
    self.defendFoodAt = self.start
    self.enemyPacman = self.start
    #Find the coordinates of barrier that seperates blue from red team
    walls = list(gameState.getWalls())
    walls_width = len(walls)
    self.midpoint = int((walls_width/2))
    
    if gameState.isOnRedTeam(self.index):
      self.midpoint = int((walls_width/2)-1)
   
    self.barrier = []
    for i, row in enumerate(walls[self.midpoint]):
        if row is False:
            self.barrier.append((int(self.midpoint), int(i)))
      
      
    CaptureAgent.registerInitialState(self, gameState)
   
  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    pos = gameState.getAgentState(self.index).getPosition()
    x, y = int(pos[0]), int(pos[1])
    if self.defendFoodAt == (x,y):
      self.defendFoodIndex += 1
    elif self.defendFoodIndex == 10 or self.foodEatenAt == self.defendFoodAt:
      self.defendFoodIndex = 0
    
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
      
      if self.isGoalState(currGameState, agentState):
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
    actions = gameState.getLegalActions(self.index)
    successors = []
    
    for action in actions:
      if action != 'Stop':
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        successors.append((pos, action, successor))

    return successors
    
  def isGoalState(self):
    return False
  
  def heauristic(self):
    return 0


class OffensiveAStarAgent(AStarAgent):
    
  def isGoalState(self, gameState, agentState):
        
    foodList = self.getFood(self.getCurrentObservation()).asList()
    pos = gameState.getAgentState(self.index).getPosition()
    x, y = int(pos[0]), int(pos[1])
    
    prevState = self.getPreviousObservation()
    px, py = self.start
    if prevState != None:
      prevPos = prevState.getAgentState(self.index).getPosition()
      px, py = int(prevPos[0]), int(prevPos[1])
    
    pacmanStuck = False
    if (x,y) == (px, py):
      pacmanStuck = True
    
    enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None]
    ghostsPos = [ghost.getPosition() for ghost in ghosts if ghost.scaredTimer < 3]
    minDisToGhost = min([self.getMazeDistance((x,y), ghost) for ghost in ghostsPos], default=999)
    avoidGhost = False
    
    if minDisToGhost < 12:
      avoidGhost = True
   
    if agentState.numCarrying < self.numFoodToEat and len(foodList) > 2 and not avoidGhost:
      distanceToFood = [self.getMazeDistance((x,y), food) for food in foodList]
      minDistance = min(distanceToFood)
      minIndex = distanceToFood.index(minDistance)
      
      return foodList[minIndex] == (x,y)
    
    elif pacmanStuck:
      return self.start == (x,y)
      
    else:
      distanceToBarrier = [self.getMazeDistance((x,y), coord) for coord in self.barrier]
      minDistance = min(distanceToBarrier)
      minIndex = distanceToBarrier.index(minDistance)
      
      return self.barrier[minIndex] == (x,y)
  
  def heauristic(self, foodList, position, agentState, gameState):
    minDistance = 0
    
    prevState = self.getPreviousObservation()
    px, py = self.start
    if prevState != None:
      prevPos = prevState.getAgentState(self.index).getPosition()
      px, py = int(prevPos[0]), int(prevPos[1])
    
    pacmanStuck = False
    if position == (px, py):
      pacmanStuck = True
    
    enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None]
    ghostsPos = [ghost.getPosition() for ghost in ghosts if ghost.scaredTimer < 3]
    minDisToGhost = min([self.getMazeDistance(position, ghost) for ghost in ghostsPos], default=999)
    avoidGhost = False
    
    if minDisToGhost < 12:
      avoidGhost = True
    
    if agentState.numCarrying < self.numFoodToEat and len(foodList) > 2 and not avoidGhost:  
      minDistance = min([self.getMazeDistance(position, food) for food in foodList])
    
    elif pacmanStuck:
      minDistance = self.getMazeDistance(position, self.start)
    else:
      minDistance = min([self.getMazeDistance(position, coord) for coord in self.barrier])
      
    return minDistance
  
class DefensiveAStarAgent(AStarAgent):
  
  def isGoalState(self, gameState, agentState):
    pos = gameState.getAgentState(self.index).getPosition()
    x, y = int(pos[0]), int(pos[1])
    
    defFoodList = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()
    foodEaten = []
    
    enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    pacmans = [a for a in enemies if a.isPacman and a.getPosition() != None]
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
      distanceToPacman = [self.getMazeDistance((x,y), pos) for pos in pacmanPos]
      minDistance = min(distanceToPacman)
      minIndex = distanceToPacman.index(minDistance)
      self.enemyPacman = pacmanPos[minIndex]
      return self.enemyPacman == (x,y)
      
    else:
      distBarrierToFood = {}
    
      for foodCoord in defFoodList:
        minDistBarrierToFood = min([self.getMazeDistance(foodCoord, coord) for coord in self.barrier])
        distBarrierToFood.update({foodCoord:minDistBarrierToFood})
    
      sortedDistBarrierToFood = list(dict(sorted(distBarrierToFood.items(), key=lambda item: item[1])))
      
      if self.defendFoodIndex < len(sortedDistBarrierToFood):
        self.defendFoodAt = sortedDistBarrierToFood[self.defendFoodIndex]
      
      return self.defendFoodAt == (x,y)
      
    

  def heauristic(self, foodList, position, agentState, gameState):
    defFoodList = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()
    minDistance = 0
    if len(defFoodList) < self.numFoodToDefend:  
      minDistance = self.getMazeDistance(position, self.foodEatenAt)
    else:
      minDistance = self.getMazeDistance(position, self.defendFoodAt)
      
    return minDistance