class Solution:
    def canMakeSubsequence(self, str1: str, str2: str) -> bool:
        src_len, tgt_len = len(str1), len(str2)
        target_char = str2[0]
        src_idx = tgt_idx = 0
        while src_idx < src_len and tgt_idx < tgt_len:
            src_char = str1[src_idx]
            if (src_char == target_char or 
                chr(ord(src_char) + 1) == target_char or 
                (src_char == 'z' and target_char == 'a')):
                tgt_idx += 1
                if tgt_idx < tgt_len:
                    target_char = str2[tgt_idx]
            src_idx += 1
            
        return tgt_idx == tgt_len


source = "abc"
target = "ad"

run = Solution()
run.canMakeSubsequence(source,target)