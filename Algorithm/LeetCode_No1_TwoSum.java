import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

/**
 * LeetCode #1 Two Sum — https://leetcode.com/problems/two-sum
 *
 * 문제 조건:
 * - 정수 배열 nums, 목표 정수 target
 * - nums에서 두 수를 더해 target이 되는 조합이 정확히 1개 있다. 두 수의 위치(인덱스)를 출력
 *
 * 제약 조건:
 * - 2 <= nums.length <= 10^4      → N^2도 시간 안에 통과
 * - -10^9 <= nums[i], target <= 10^9 → 두 수의 합도 int 범위 안 (long 불필요)
 *
 * 해결 순서 (LeetCode 실행 시간):
 * 1. 처음에는 다 해보자 (이중 for문, N^2)                → 90ms   {@link #twoSumBruteForce}
 * 2. HashMap에 전부 넣고, 한 번 더 돌며 짝을 찾기 (2N)   → 12ms   {@link #twoSumTwoPass}
 * 3. HashMap에 넣으면서 바로 짝을 찾기 (N, 최종 제출)    → 1~6ms  {@link #twoSum}
 *
 * LeetCode에는 twoSum이 있는 Solution 클래스만 제출하면 된다.
 * 직접 실행: javac LeetCode_No1_TwoSum.java && java -cp . Solution
 */
class Solution {

    /**
     * 최종 제출 코드: 앞에서부터 보면서
     * 1) 짝(target - 지금 수)이 이미 HashMap에 있으면 정답. HashMap에 있는 쪽이 먼저 나온 수라서 순서를 바꿔 출력
     * 2) 없으면 지금 수를 HashMap에 넣는다 (key: 값, value: 인덱스)
     */
    public int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int partner = target - nums[i];
            Integer partnerIndex = seen.get(partner);
            if (partnerIndex != null) {
                return new int[] {partnerIndex, i};
            }
            seen.put(nums[i], i);
        }
        throw new IllegalArgumentException("No Answer");
    }

    /** 1. 처음에는 다 해보자: 모든 두 수 조합을 확인 (N^2) */
    public int[] twoSumBruteForce(int[] nums, int target) {
        for (int i = 0; i < nums.length; i++) {          // 앞에서부터 끝까지
            for (int j = i + 1; j < nums.length; j++) {  // 그 수 뒤에 있는 수 전부
                if (nums[i] + nums[j] == target) {
                    return new int[] {i, j};
                }
            }
        }
        throw new IllegalArgumentException("No Answer");
    }

    /** 2. HashMap에 전부 넣은 뒤, 한 번 더 돌며 짝을 찾기 (2N) */
    public int[] twoSumTwoPass(int[] nums, int target) {
        Map<Integer, Integer> indexOf = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            indexOf.put(nums[i], i);
        }
        for (int i = 0; i < nums.length; i++) {
            Integer partnerIndex = indexOf.get(target - nums[i]);
            if (partnerIndex != null && partnerIndex != i) {  // 같은 수를 두 번 쓰는 경우는 제외
                return new int[] {i, partnerIndex};
            }
        }
        throw new IllegalArgumentException("No Answer");
    }

    public static void main(String[] args) {
        Solution s = new Solution();
        int[][] nums = {{2, 7, 11, 15}, {3, 2, 4}, {3, 3}};
        int[] targets = {9, 6, 6};
        for (int t = 0; t < nums.length; t++) {
            System.out.printf("%s, target %d -> %s / %s / %s%n",
                    Arrays.toString(nums[t]), targets[t],
                    Arrays.toString(s.twoSum(nums[t], targets[t])),
                    Arrays.toString(s.twoSumBruteForce(nums[t], targets[t])),
                    Arrays.toString(s.twoSumTwoPass(nums[t], targets[t])));
        }
    }
}
