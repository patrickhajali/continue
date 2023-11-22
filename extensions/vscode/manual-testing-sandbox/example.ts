function mergeSortAlgorithm() {
  
  // TODO: implement
function mergeSortAlgorithm(arr: number[]): number[] {
  if (arr.length <= 1) {
    return arr;
  }
  const middle = Math.floor(arr.length / 2);
  const left = arr.slice(0, middle);
  const right = arr.slice(middle);

  return merge(mergeSortAlgorithm(left), mergeSortAlgorithm(right));
}

function merge(left: number[], right: number[]): number[] {
  let resultArray = [], leftIndex = 0, rightIndex = 0;

  while (leftIndex < left.length && rightIndex < right.length) {
    if (left[leftIndex] < right[rightIndex]) {
      resultArray.push(left[leftIndex]);
      leftIndex++;
    } else {
      resultArray.push(right[rightIndex]);
      rightIndex++;
    }
  }

  // Return the result array concatenated with the remaining elements of the left and right arrays
  return resultArray
          .concat(left.slice(leftIndex))
          .concat(right.slice(rightIndex));
}
function mergeSortAlgorithm(arr: number[]): number[] {
  if (arr.length <= 1) {
    return arr;
  }
  const middle = Math.floor(arr.length / 2);
  const left = arr.slice(0, middle);
  const right = arr.slice(middle);

  return merge(mergeSortAlgorithm(left), mergeSortAlgorithm(right));
}

function merge(left: number[], right: number[]): number[] {
  let resultArray = [], leftIndex = 0, rightIndex = 0;

  while (leftIndex < left.length && rightIndex < right.length) {
    if (left[leftIndex] < right[rightIndex]) {
      resultArray.push(left[leftIndex]);
      leftIndex++;
    } else {
      resultArray.push(right[rightIndex]);
      rightIndex++;
    }
  }

  // Return the result array concatenated with the remaining elements of the left and right arrays
  return resultArray
          .concat(left.slice(leftIndex))
          .concat(right.slice(rightIndex));
}
}
}
