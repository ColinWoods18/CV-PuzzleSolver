import numpy as np
import cv2
import time
import math
from scipy import stats
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, peak_widths
import random

import piece

class PuzzlePieces:
    def __init__(self, puzzleName, numPieces, hueRange, satRange, valRange):
        self.pieces = []
        self.puzzleName = puzzleName
        filename = f'../input/{puzzleName}.jpg'
        img = cv2.imread(filename)
        self.img = img
        self.numPieces = numPieces
        self.contours = []
        self.corners = []
        self.hueRange = hueRange
        self.satRange = satRange
        self.valRange = valRange
    def findContours(self):
        self.contours = getPieces(self.img, self.numPieces, self.hueRange, self.satRange, self.valRange)
        
        for i in range(len(self.contours)):
            piece2 = piece.Piece(i, self.img)
            piece2.setContour(self.contours[i])
            self.pieces.append(piece2)
    
    def showPieces(self):
        if len(self.contours) == 0:
            self.findContours()
        pieceImg = drawPieces(self.img, self.contours)
        cv2.imshow(f'showPieces {self.puzzleName}',  cv2.rotate(cv2.resize(pieceImg, (pieceImg.shape[1]//4, 
                    pieceImg.shape[0]//4), interpolation = cv2.INTER_AREA), cv2.ROTATE_90_CLOCKWISE))
        cv2.waitKey()
        return pieceImg
    
    def findCorners(self):
        if len(self.contours) == 0:
            self.findContours()
        self.corners = cornerDetection(self.contours)

        for i in range(len(self.corners)):
            piece = self.pieces[i]
            piece.setCorners(self.corners[i])
    
    def showCorners(self):
        if len(self.corners) == 0:
            self.findCorners()
        pieceImg = self.img.copy()
        for i in range(len(self.corners)):
            corner = self.corners[i]    
            for j in range(len(corner)):
                cv2.circle(pieceImg, (int(corner[j][1]), int(corner[j][2])), 10, (0, 255, 255), thickness=-1, lineType=cv2.FILLED)
                cv2.line(pieceImg, (int(corner[j][1]), int(corner[j][2])), (int(corner[j-1][1]), int(corner[j-1][2])), 
                        (0,0,255), thickness=4)
        cv2.imshow(f'showCorners {self.puzzleName}',  cv2.rotate(cv2.resize(pieceImg, (pieceImg.shape[1]//4, 
                    pieceImg.shape[0]//4), interpolation = cv2.INTER_AREA), cv2.ROTATE_90_CLOCKWISE))
        cv2.waitKey()
        return pieceImg

    def findEdges(self):
        if len(self.corners) == 0:
            self.findCorners()
        for piece in self.pieces:
            piece.findEdges()

    def showEdges(self):
        if len(self.corners) == 0:
            self.findCorners()
        pieceImg = self.img.copy()
        for piece in self.pieces:
            piece.drawEdges(pieceImg)
        cv2.imshow(f'showEdges {self.puzzleName}',  cv2.rotate(cv2.resize(pieceImg, (pieceImg.shape[1]//4, 
                    pieceImg.shape[0]//4), interpolation = cv2.INTER_AREA), cv2.ROTATE_90_CLOCKWISE))
        cv2.waitKey()
        return pieceImg

    def findMinDistEdge(self, without):
        minDist = float('inf')
        minDistEdge1 = None
        minDistPiece1 = None
        minDistEdge2 = None
        minDistPiece2 = None
        pieceImg = self.img.copy()
        for i in range(len(self.pieces)):
            edgeIndexes = np.array(range(4))
            withoutEdges = without[:,1][np.where(without[:,0] == i)]
            edgeIndexes = np.setdiff1d(edgeIndexes, withoutEdges)
            for j in edgeIndexes:
                piece1 = self.pieces[i]
                edge, piece, dist = piece1.findClosestEdge(j, self.pieces, without)
                if piece == None:
                    continue
                piece2 = self.pieces[piece]
                if dist < minDist:
                    minDist = dist
                    minDistEdge1 = j
                    minDistPiece1 = i
                    minDistEdge2 = edge
                    minDistPiece2 = piece
        return minDistEdge1, minDistPiece1, minDistEdge2, minDistPiece2, minDist

    def puzzleSolver(self):
        pieceImg = np.zeros_like(self.img)
        without = np.array([[-1,-1]])
        while True:
            edge1, piece1, edge2, piece2, dist = self.findMinDistEdge(without)
            if edge1 == None or piece1 == None:
                cv2.waitKey()
                break

            without = np.vstack((without, np.array([piece1, edge1])))
            without = np.vstack((without, np.array([piece2, edge2])))

            self.pieces[piece1].drawClosestEdge(pieceImg, edge1, self.pieces[piece2], edge2)
            cv2.imshow(f'closestEdge {self.puzzleName}',  cv2.rotate(cv2.resize(pieceImg, (pieceImg.shape[1]//4, 
                pieceImg.shape[0]//4), interpolation = cv2.INTER_AREA), cv2.ROTATE_90_CLOCKWISE))
            k = cv2.waitKey(100)&0xff
            if k == 27:
                break
        return pieceImg

def getPieces( img, numPieces, hueRange, satRange, valRange ):
    #mask based on a range of colors for the background
    #img2 = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img2 = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    #cv2.imshow('hsv',  cv2.rotate(cv2.resize(img2, (img.shape[1]//4, img.shape[0]//4), interpolation = cv2.INTER_AREA),
    #                    cv2.ROTATE_90_CLOCKWISE))
    cv2.waitKey()
    #reshape image into just 3 by num pixels list of the colors
    colors = img2.reshape(-1, 3)
    #find the most common color in that list
    bg = stats.mode(colors)[0][0]

    #make a mask based on the most common color
    mins = bg - np.array([hueRange, satRange, valRange])
    maxs = bg + np.array([hueRange, satRange, valRange])
    img3 = cv2.inRange(img2, mins, maxs)
    #cv2.imshow('hsv',  cv2.rotate(cv2.resize(img3, (img.shape[1]//4, img.shape[0]//4), interpolation = cv2.INTER_AREA),
    #                    cv2.ROTATE_90_CLOCKWISE))
    cv2.waitKey()
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    #img3 = cv2.erode(img3, kernel, iterations=2)
    img3 = cv2.dilate(img3, kernel, iterations=2)

    #find contours in the mask
    contours, hierarchy = cv2.findContours(img3, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    #cv2.imshow('hsv',  cv2.rotate(cv2.resize(img, (img.shape[1]//4, img.shape[0]//4), interpolation = cv2.INTER_AREA),
    #                    cv2.ROTATE_90_CLOCKWISE))
    cv2.waitKey()
    #sort the contours by area, choose the biggest ones for the pieces
    # note that the largest contour is just the entire board
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    contours = contours[1:numPieces+1]
    
    return contours

def drawPieces( img, contours ):
    #put the contour areas on a blank background as white
    img2 = np.zeros_like(img)
    cv2.drawContours(img2, contours, -1, (255,255,255), thickness=-1)
    #take the white areas and include those areas from img
    img3 = img & img2
    return img3

def cart2pol(x, y):
    rho = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    return rho, phi

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y

def closestDistPhi( phi1, phi2 ):
    if phi1 < 0:
        phi1 = 2*math.pi + phi1
    if phi2 < 0:
        phi2 = 2*math.pi + phi2
    dist = abs(phi1 - phi2)
    if dist > math.pi:
        if phi1 > math.pi:
            phi1 = -(2*math.pi - phi1)
        if phi2 > math.pi:
            phi2 = -(2*math.pi - phi2)
        dist = abs(phi1 - phi2)    
    return dist

def cornerDetection(contours):
    corners = np.empty((len(contours),4,3), dtype=np.int32)
    for i in range(len(contours)):
        cnt = contours[i]
        center = np.mean(cnt[:,0], axis=0)

        cntCen = np.empty_like(cnt)
        for j in range(len(cnt)):
            cntCen[j] = [cnt[j][0] - center]

        rho, phi = cart2pol(cntCen[:,0,0], cntCen[:,0,1])
        peaks, _ = find_peaks(rho, distance=50)
        
        if (peaks[0] + len(rho)) - peaks[-1] <= 50:
            if rho[peaks[0]] < rho[peaks[-1]]:
                peaks = peaks[1:]
            else:
                peaks = peaks[:-1]

        rhoMax = np.max(rho[peaks])

        diffLeft = rhoMax - rhoMax * rho[(peaks-30) % len(rho)] / rho[peaks]
        diffLeft[np.where(diffLeft < 0)] = 0
        diffRight = rhoMax - rhoMax * rho[(peaks+30) % len(rho)] / rho[peaks]
        diffRight[np.where(diffRight < 0)] = 0
        sharpness = diffLeft*diffRight
        
        #for smaller puzzle pieces
        #cornerPeaks = np.argsort(sharpness)[-4:]
        
        #for bigger puzzle pieces
        cornerPeaks = np.where(sharpness > 0)

        sharpness = sharpness[cornerPeaks]

        peaks = peaks[cornerPeaks]
                
        #plt.plot(rho, '.')
        #plt.plot(peaks, rho[peaks], 'x', c='orange')
        #plt.show()

        order = np.argsort([phi[peaks]])

        peaks = peaks[order][0]
        sharpness = sharpness[order][0]
        sharpnessSorted = np.flip(np.argsort(sharpness))

        peaks2 = np.empty((0,), dtype=np.int32)
        
        '''
        for smaller puzzles
        '''
        start = sharpnessSorted[0]
        peaks2 = np.append(peaks2, start)
        nextCorner = start
        while True:
            index = nextCorner
            phi1 = phi[peaks[index]]
            dists = np.empty((0,), dtype=np.float64)
            indexes = np.empty((0,), dtype=np.int32)
            for j in range(len(peaks)):
                if j in peaks2:
                    continue
                phi2 = phi[peaks[j]]
                dists = np.append(dists, closestDistPhi(phi1, phi2))
                indexes = np.append(indexes, j)
            if len(dists) > 0 and np.min(abs(dists - math.pi/2)) < math.pi/8:
                nextCorner = indexes[np.argmin(abs(dists - math.pi/2))]
                peaks2 = np.append(peaks2, nextCorner)
            elif len(dists) > 0:
                nextCorner = (nextCorner + 1) % len(peaks)
                peaks2 = np.append(peaks2, nextCorner)
            else:
                break
            if len(peaks2) >= 4:
                break
        peaks = peaks[peaks2]
        '''
        end section
        '''
        order = np.argsort([phi[peaks]])
        peaks = peaks[order][0]
        
        cornerX = cnt[:,0,0][peaks]
        cornerY = cnt[:,0,1][peaks]
        
        corners[i,:,0] = peaks
        corners[i,:,1] = cornerX
        corners[i,:,2] = cornerY
    return corners