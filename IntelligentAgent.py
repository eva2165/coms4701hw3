from BaseAI  import BaseAI
from Grid    import Grid

import time
import math

TIME_LIMIT = 0.2
EPSILON = 0.05
STOP_TIME = TIME_LIMIT - EPSILON

TWO_PROB = 0.9
FOUR_PROB = 1 - TWO_PROB

# Weights of utility measures
LST =  1000000.0   # If this board has no available moves
NES =      600.0   # Number of empty spaces
PES =    14000.0   # Penalize for dangerously low no. of empty spaces
ELG =      400.0   # Large values on edges
NMT =    12000.0   # Non-monotonic rows or columns. Stronger the larger the numbers involved
PMG =      900.0   # Potential merges (no. equal and adjacent values)
RUF =      400.0   # Roughness, the total difference of value between each active tile

EDGE_CELLS = [(0,0), (1,0), (2,0), (3,0), (3,1), (3,2), (3,3), \
              (2,3), (1,3), (0,3), (0,2), (0,1)]

class IntelligentAgent(BaseAI):
    
    class Node:
        def __init__(self, grid, depth):
            self.grid = grid
            self.depth = depth
    
    def getMove(self, grid):
        
        self.starttime = time.process_time()
        self.ids_depth = 0
        
        move = None
        
        while True:
            decided = self.decision(grid)
            if (decided == None):
                break
            else:
                move = decided
            self.ids_depth += 1
        
        return move
    
    def timesup(self):
        return (time.process_time() - self.starttime) > STOP_TIME
    
    def decision(self, grid):
        
        alpha = -math.inf
        beta = math.inf
        
        moves = grid.getAvailableMoves()
        moves = [(i[0], self.Node(i[1], 1)) for i in moves]
        
        maxval = -math.inf
        bestmove = 0
        
        for m in moves:
            val = self.expminimize(m[1], alpha, beta)
            if (val == None):
                return None
            if (val > maxval):
                bestmove = m[0]
                maxval = val
            if (maxval >= beta): break
            alpha = max(alpha, maxval)
        
        return bestmove
    
    def maximize(self, node, alpha, beta):
        
        if self.timesup():
            return None
        
        if (node.depth > self.ids_depth):
            return self.utility(node.grid)
        
        maxval = -math.inf
        
        options = self.udlrswipes(node)
        
        if len(options) == 0:
            return self.utility(node.grid)
        
        for n in options:
            val = self.expminimize(n, alpha, beta)
            if (val == None):
                return None
            maxval = max(maxval, val)
            if (maxval >= beta): break
            alpha = max(alpha, maxval)
        
        return maxval
    
    def expminimize(self, node, alpha, beta):
        
        if self.timesup():
            return None
        
        if (node.depth > self.ids_depth):
            return self.utility(node.grid)
        
        minval = math.inf
        
        options = self.oppplacements(node)
        
        if len(options) == 0:
            return self.utility(node.grid)
        
        for n in options:
            chanceleft = self.maximize(n[0], alpha, beta)
            if (chanceleft == None): return None
            chanceright = self.maximize(n[1], alpha, beta)
            if (chanceright == None): return None
            val = int((TWO_PROB * chanceleft) + (FOUR_PROB * chanceright))
            minval = min(minval, val)
            if (minval <= alpha): break
            beta = min(beta, minval)
        
        return minval
    
    def udlrswipes(self, node):
        return [ self.Node(i[1], node.depth+1) \
                for i in node.grid.getAvailableMoves()]
    
    def oppplacements(self, node):
        
        cells = node.grid.getAvailableCells()
        
        # Create a list of 2-length lists of nodes, where the first is if
        # a 2 were placed, the second if a 4 were placed
        placements = [[self.Node(node.grid.clone(), node.depth+1), \
          self.Node(node.grid.clone(), node.depth+1)]] * len(cells)
        for i in range(len(cells)):
            placements[i][0].grid.insertTile(cells[i], 2)
            placements[i][1].grid.insertTile(cells[i], 4)
        
        return placements
    
    def utility(self, grid):
        return 1000 + int( - ( self.boardlost(grid, LST) ) \
                    - ( PES * self.penemptyspaces(grid) )
                    + ( NES * self.numemptyspaces(grid)  ) \
                    + ( ELG * self.edgelargeness(grid)   ) \
                    - ( NMT * self.nonmonotonicity(grid) ) \
                    + ( PMG * self.potentialmerges(grid) ) \
                    - ( RUF * self.roughness(grid)       ) )
    
    # Returns the weight if the board has no possible moves, 0 if not
    def boardlost(self, grid, weight):
        if grid.canMove():
            return 0.0
        return weight
    
    def numemptyspaces(self, grid):
        return ( len(grid.getAvailableCells()) / 16 )
    
    def penemptyspaces(self, grid):
        empties = len(grid.getAvailableCells())
        if empties > 5:
            return 0.0
        elif empties == 5:
            return 0.1
        elif empties == 4:
            return 0.2
        elif empties == 3:
            return 0.4
        elif empties == 2:
            return 0.6
        elif empties == 1:
            return 0.8
        elif empties == 0:
            return 1.0
        else:
            return 0.0
    
    def edgelargeness(self, grid):
        
        values = 0
        
        for cell in EDGE_CELLS:
            values += (grid.getCellValue(cell) * 2)
        
        return ( values / 1000 )
    
    def nonmonotonicity(self, grid):
        
        nonmonval = 0
        
        for x in range(4):
            column = [grid.getCellValue((x,y)) for y in range(4)]
            if not self.ismonotonic(column):
                for i in column:
                    nonmonval += i * 2
        
        for y in range(4):
            row = [grid.getCellValue((x,y)) for x in range(4)]
            if not self.ismonotonic(row):
                for i in row:
                    nonmonval += i * 2
        
        return ( nonmonval / 1000 )
            
    def ismonotonic(self, sequence):
        
        alldecreasing = True
        allincreasing = True
        
        for i in range(3):
            if sequence[i] < sequence[i+1]:
                alldecreasing = False
        
        for i in range(3):
            if sequence[i] > sequence[i+1]:
                allincreasing = False
        
        return alldecreasing or allincreasing
    
    def potentialmerges(self, grid):
        
        adjacencies = 0
        
        for x in range(4):
            for y in range(4):
                cellval = grid.getCellValue((x,y))
                if cellval != 0:
                    
                    # Up direction
                    distance = 1
                    while y - distance >= 0:
                        otherval = grid.getCellValue((x,y - distance))
                        if cellval == otherval:
                            adjacencies += 1
                            break
                        elif otherval != 0:
                            break
                        distance += 1
                    
                    # Down direction
                    distance = 1
                    while y + distance <= 3:
                        otherval = grid.getCellValue((x,y + distance))
                        if cellval == otherval:
                            adjacencies += 1
                            break
                        elif otherval != 0:
                            break
                        distance += 1
                    
                    # Left direction
                    distance = 1
                    while x - distance >= 0:
                        otherval = grid.getCellValue((x - distance,y))
                        if cellval == otherval:
                            adjacencies += 1
                            break
                        elif otherval != 0:
                            break
                        distance += 1
                    
                    # Right direction
                    distance = 1
                    while x + distance <= 3:
                        otherval = grid.getCellValue((x + distance,y))
                        if cellval == otherval:
                            adjacencies += 1
                            break
                        elif otherval != 0:
                            break
                        distance += 1
        
        # We have double the true number of adjacencies as each pair finds each
        # other two times
        adjacencies = adjacencies // 2
        
        return ( adjacencies / 24 )
    
    # Returns a value from 0.0 to 1.0, the non-smoothness of the grid
    def roughness(self, grid):
        
        differences = 0.0
        
        for x in range(4):
            for y in range(3):
                first  = grid.getCellValue((x, y))
                second = grid.getCellValue((x, y+1))
                if (first != 0) and (second != 0):
                    differences += abs(math.log2(first) - math.log2(second))
        
        for y in range(4):
            for x in range(3):
                first  = grid.getCellValue((x, y))
                second = grid.getCellValue((x+1, y))
                if (first != 0) and (second != 0):
                    differences += abs(math.log2(first) - math.log2(second))
        
        return ( differences / 192.0 )