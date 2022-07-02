class Solution {
    public int[] twoSum(int[] nums, int target) {

        /* url : https://leetcode.com/problems/two-sum 
        */

        /*    최종 제출코드   */

        /* HashMap에 넣으면서 값을 구해보기   
           1) N번 돌면서 값을 찾아보기
               1-1) 답 출력할때 순서 거꾸로 하기 (HashMap에 있다는 얘기는 값이 이미 들어갔다 -> 먼저 나옴)
           2) 답이 아니면 HashMap에 넣기(put)
       */

        Map<Integer, Integer> hashMap = new HashMap<>();
        for (int i = 0; i<nums.length; i++){
            int ans = target - nums[i];
            if (hashMap.containsKey(ans)){
                return new int[] {hashMap.get(ans), i};
            }
            hashMap.put(nums[i],i);
        }
        
        throw new IllegalArgumentException("No Answer");

        /*    최종 제출코드  끝 */


       /*    풀이 과정   */
        /*
        문제 조건 : 
        - 정수 배열 nums
        - 목표 정수 target
        - nums에서 정수 2개를 더해서 target 이 되는 값 1개 존재
          2개의 배열에서의 위치를 출력하라
          
        제약 조건 : 
        2 <= nums.length <= 10^4      시간 : N^2해도 충분
        -10^9 <= nums[i] <= 10^9      long말고 int로 충분
        -10^9 <= target <= 10^9
        
        해결 순서 :
        1. 처음에는 다 해보자  -> N^2 방법 -> 90ms
        
        2. HashMap에 
           1) N번 돌면서 데이터 전부 넣고
           2) N번 돌면서 값을 빠르게 찾기 -> 12ms 
           
        3. HashMap에 넣으면서 값을 구해보기   -> 1~6 ms
           1) N번 돌면서 값을 찾아보기
           2) 답이 아니면 HashMap에 넣기(put)
           3) 답 출력할때 순서 거꾸로 하기 (HashMap에 있다는 얘기는 값이 이미 들어갔다 -> 먼저 나옴)

       1. 처음에는 다 해보자  
        // 앞에서 부터 끝까지 다 보겠다
        for (int i = 0; i < nums.length; i++){
            // 그 수 뒤에 있는 수 전부 보겠다
            for (int j = i+1; j < nums.length; j++){
                // 두 수의 합이 target이면 정답 
                if (nums[i] + nums[j] == target){
                    return new int[] {i, j};
                }
            }
        }


        2. HashMap에서 N*2번 돌기
        Map<Integer, Integer> hashMap = new HashMap<Integer, Integer>();
        
        // 1) HashMap에 nums 배열 넣기
        for (int i = 0; i<nums.length; i++){
            // key : 값 , value : index
            hashMap.put(nums[i],i);
        }
        
        // 2) HashMap에서 빠르게 값 찾기
        for (int i = 0; i<nums.length; i++){
            
            // 2-1) 예외조건 인덱스가 같은 경우는 예외 처리
            int ans = target - nums[i];
            if (hashMap.containsKey(ans) 
                && i != hashMap.get(ans) ){
                return new int[] {i, hashMap.get(ans)};
            }
            
        }
        */


    }

}