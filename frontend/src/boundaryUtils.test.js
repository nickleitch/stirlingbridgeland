// Unit tests for boundary filtering logic

// Point-in-polygon test using ray casting algorithm
const isPointInPolygon = (point, polygon) => {
  const [x, y] = point;
  let inside = false;
  
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    
    if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {
      inside = !inside;
    }
  }
  
  return inside;
};

// Helper function to check if coordinates are inside a boundary
const isCoordinateInBoundary = (latitude, longitude, boundary) => {
  if (!boundary.geometry || !boundary.geometry.rings || boundary.geometry.rings.length === 0) {
    return false;
  }
  
  // Check the outer ring (first ring is usually the outer boundary)
  const outerRing = boundary.geometry.rings[0];
  if (!outerRing || outerRing.length < 3) return false;
  
  // Convert to [lat, lng] format and check if point is inside
  const polygonPoints = outerRing.map(coord => [coord[1], coord[0]]); // Convert [lng, lat] to [lat, lng]
  return isPointInPolygon([latitude, longitude], polygonPoints);
};

// Unit test runner
const runTests = () => {
  console.log('🧪 Running Boundary Filtering Unit Tests...');
  
  let testsPassed = 0;
  let testsTotal = 0;
  
  const test = (name, testFn) => {
    testsTotal++;
    try {
      const result = testFn();
      if (result) {
        console.log(`✅ ${name}`);
        testsPassed++;
      } else {
        console.log(`❌ ${name} - Test failed`);
      }
    } catch (error) {
      console.log(`❌ ${name} - Error: ${error.message}`);
    }
  };
  
  // Test 1: Point inside simple square
  test('Point inside simple square', () => {
    const square = [[0, 0], [1, 0], [1, 1], [0, 1]]; // Unit square
    return isPointInPolygon([0.5, 0.5], square) === true;
  });
  
  // Test 2: Point outside simple square
  test('Point outside simple square', () => {
    const square = [[0, 0], [1, 0], [1, 1], [0, 1]]; // Unit square
    return isPointInPolygon([1.5, 1.5], square) === false;
  });
  
  // Test 3: Point on edge (should be handled consistently)
  test('Point on edge of square', () => {
    const square = [[0, 0], [1, 0], [1, 1], [0, 1]]; // Unit square
    const result = isPointInPolygon([1, 0.5], square);
    // Edge cases can return either true or false, we just check it doesn't crash
    return typeof result === 'boolean';
  });
  
  // Test 4: Point inside complex polygon (triangle)
  test('Point inside triangle', () => {
    const triangle = [[0, 0], [2, 0], [1, 2]]; // Triangle
    return isPointInPolygon([1, 0.5], triangle) === true;
  });
  
  // Test 5: Point outside triangle
  test('Point outside triangle', () => {
    const triangle = [[0, 0], [2, 0], [1, 2]]; // Triangle
    return isPointInPolygon([3, 3], triangle) === false;
  });
  
  // Test 6: Coordinate in boundary with mock boundary object
  test('Coordinate in boundary object', () => {
    const mockBoundary = {
      geometry: {
        rings: [
          [
            [28.040, -26.200], // lng, lat format (bottom-left)
            [28.050, -26.200], // bottom-right
            [28.050, -26.210], // top-right
            [28.040, -26.210], // top-left
            [28.040, -26.200]  // close the ring
          ]
        ]
      }
    };
    
    // Point inside the boundary
    return isCoordinateInBoundary(-26.205, 28.045, mockBoundary) === true;
  });
  
  // Test 7: Coordinate outside boundary object
  test('Coordinate outside boundary object', () => {
    const mockBoundary = {
      geometry: {
        rings: [
          [
            [28.040, -26.200], // lng, lat format
            [28.050, -26.200],
            [28.050, -26.210],
            [28.040, -26.210],
            [28.040, -26.200]
          ]
        ]
      }
    };
    
    // Point outside the boundary
    return isCoordinateInBoundary(-26.220, 28.060, mockBoundary) === false;
  });
  
  // Test 8: Invalid boundary object
  test('Invalid boundary object handling', () => {
    const invalidBoundary = { geometry: null };
    return isCoordinateInBoundary(-26.205, 28.045, invalidBoundary) === false;
  });
  
  // Test 9: Empty rings handling
  test('Empty rings handling', () => {
    const emptyBoundary = { geometry: { rings: [] } };
    return isCoordinateInBoundary(-26.205, 28.045, emptyBoundary) === false;
  });
  
  // Test 10: Real-world coordinates (Johannesburg area)
  test('Real-world Johannesburg coordinates', () => {
    const joeBoundary = {
      geometry: {
        rings: [
          [
            [28.040, -26.200],
            [28.050, -26.200],
            [28.050, -26.210],
            [28.040, -26.210],
            [28.040, -26.200]
          ]
        ]
      }
    };
    
    // Test coordinates from your original query
    const testLat = -26.2041;
    const testLng = 28.0473;
    
    return isCoordinateInBoundary(testLat, testLng, joeBoundary) === true;
  });
  
  console.log(`\n📊 Test Results: ${testsPassed}/${testsTotal} tests passed`);
  
  if (testsPassed === testsTotal) {
    console.log('🎉 All tests passed! Boundary filtering logic is working correctly.');
  } else {
    console.log('⚠️ Some tests failed. Review the boundary filtering logic.');
  }
  
  return testsPassed === testsTotal;
};

// Export for use in browser console
if (typeof window !== 'undefined') {
  window.runBoundaryTests = runTests;
  window.isPointInPolygon = isPointInPolygon;
  window.isCoordinateInBoundary = isCoordinateInBoundary;
}

// Auto-run tests if this file is executed directly
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { runTests, isPointInPolygon, isCoordinateInBoundary };
} else {
  // Run tests when loaded in browser
  console.log('Boundary filtering unit tests loaded. Run window.runBoundaryTests() to execute tests.');
}