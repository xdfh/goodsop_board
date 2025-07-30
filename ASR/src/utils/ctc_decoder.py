# Copyright (c) 2020 Mobvoi Inc. (authors: Binbin Zhang, Di Wu)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List, Tuple

import torch


class CTC:
    """A simplified CTC decoder class, containing only the greedy search functionality."""

    def __init__(self,
                 char_dict_path: str,
                 blank_id: int = 0):
        self.blank_id = blank_id
        self.char_dict = {}
        with open(char_dict_path, 'r', encoding="utf-8") as f:
            for line in f:
                arr = line.strip().split()
                assert len(arr) == 2
                self.char_dict[int(arr[1])] = arr[0]

    def greedy_search(self, hyps: torch.Tensor) -> List[Tuple[str, List[int]]]:
        """
        Performs CTC greedy search.
        
        Args:
            hyps (torch.Tensor): The output tensor from the model, shape (B, T, D).
        
        Returns:
            A list of tuples, where each tuple contains the decoded text and the list of token IDs.
        """
        batch_size = hyps.shape[0]
        topk_hyps, _ = hyps.topk(1, dim=2)  # (B, T, 1)
        topk_hyps = topk_hyps.squeeze(2)  # (B, T)
        results = []
        for i in range(batch_size):
            hyp = topk_hyps[i]
            
            # Remove consecutive duplicates and blank tokens
            unique_arr = []
            for j, c in enumerate(hyp):
                c_item = c.item()
                if c_item != self.blank_id:
                    if j == 0 or c_item != hyp[j - 1].item():
                        unique_arr.append(c_item)

            text = self.ids2text(unique_arr)
            results.append((text, unique_arr))
        return results

    def ids2text(self, ids: List[int]) -> str:
        """Converts a list of token IDs to a string."""
        text = ""
        for i in ids:
            if i in self.char_dict:
                text += self.char_dict[i]
        return text 