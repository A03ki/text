import torch
from test.common.torchtext_test_case import TorchtextTestCase
from ..common.assets import get_asset_path
from torchtext.experimental.transforms import (
    VocabTransform,
)
from torchtext.experimental.vocab import (
    vocab_from_file,
    vocab_from_raw_text_file,
)
import shutil
import tempfile
import os
from torchtext.experimental.vectors import (
    GloVe,
    vectors,
)


class TestTransformsWithAsset(TorchtextTestCase):
    def test_vocab_transform(self):
        asset_name = 'vocab_test2.txt'
        asset_path = get_asset_path(asset_name)
        with open(asset_path, 'r') as f:
            vocab_transform = VocabTransform(vocab_from_file(f))
            self.assertEqual(vocab_transform([['of', 'that', 'new'], ['of', 'that', 'new', 'that']]),
                             [[7, 18, 24], [7, 18, 24, 18]])
            jit_vocab_transform = torch.jit.script(vocab_transform.to_ivalue())
            self.assertEqual(jit_vocab_transform([['of', 'that', 'new'], ['of', 'that', 'new', 'that']]),
                             [[7, 18, 24], [7, 18, 24, 18]])

    def test_errors_vectors_python(self):
        tokens = []
        vecs = torch.empty(0, dtype=torch.float)

        with self.assertRaises(ValueError):
            # Test proper error raised when passing in empty tokens and vectors and
            # not passing in a user defined unk_tensor
            vectors(tokens, vecs)

        tensorA = torch.tensor([1, 0, 0], dtype=torch.int8)
        tokens = ['a']
        vecs = tensorA.unsqueeze(0)

        with self.assertRaises(TypeError):
            # Test proper error raised when vector is not of type torch.float
            vectors(tokens, vecs)

        with tempfile.TemporaryDirectory() as dir_name:
            # Test proper error raised when incorrect filename or dim passed into GloVe
            asset_name = 'glove.6B.zip'
            asset_path = get_asset_path(asset_name)
            data_path = os.path.join(dir_name, asset_name)
            shutil.copy(asset_path, data_path)

            with self.assertRaises(ValueError):
                # incorrect name
                GloVe(name='UNK', dim=50, root=dir_name, validate_file=False)

            with self.assertRaises(ValueError):
                # incorrect dim
                GloVe(name='6B', dim=500, root=dir_name, validate_file=False)

    def test_glove(self):
        # copy the asset file into the expected download location
        # note that this is just a zip file with the first 100 entries of the GloVe 840B dataset
        asset_name = 'glove.840B.300d.zip'
        asset_path = get_asset_path(asset_name)

        with tempfile.TemporaryDirectory() as dir_name:
            data_path = os.path.join(dir_name, asset_name)
            shutil.copy(asset_path, data_path)
            vectors_obj = GloVe(root=dir_name, validate_file=False)
            jit_vectors_obj = torch.jit.script(vectors_obj.to_ivalue())

            # The first 3 entries in each vector.
            expected_glove = {
                'the': [0.27204, -0.06203, -0.1884],
                'people': [-0.19686, 0.11579, -0.41091],
            }

            for word in expected_glove.keys():
                self.assertEqual(vectors_obj[word][:3], expected_glove[word])
                self.assertEqual(jit_vectors_obj[word][:3], expected_glove[word])

    def test_glove_different_dims(self):
        # copy the asset file into the expected download location
        # note that this is just a zip file with 1 line txt files used to test that the
        # correct files are being loaded
        asset_name = 'glove.6B.zip'
        asset_path = get_asset_path(asset_name)

        with tempfile.TemporaryDirectory() as dir_name:
            data_path = os.path.join(dir_name, asset_name)
            shutil.copy(asset_path, data_path)

            glove_50d = GloVe(name='6B', dim=50, root=dir_name, validate_file=False)
            glove_100d = GloVe(name='6B', dim=100, root=dir_name, validate_file=False)
            glove_200d = GloVe(name='6B', dim=200, root=dir_name, validate_file=False)
            glove_300d = GloVe(name='6B', dim=300, root=dir_name, validate_file=False)
            vectors_objects = [glove_50d, glove_100d, glove_200d, glove_300d]

            # The first 3 entries in each vector.
            expected_glove_50d = {
                'the': [0.418, 0.24968, -0.41242],
            }
            expected_glove_100d = {
                'the': [-0.038194, -0.24487, 0.72812],
            }
            expected_glove_200d = {
                'the': [-0.071549, 0.093459, 0.023738],
            }
            expected_glove_300d = {
                'the': [0.04656, 0.21318, -0.0074364],
            }
            expected_gloves = [expected_glove_50d, expected_glove_100d, expected_glove_200d, expected_glove_300d]

            for vectors_obj, expected_glove in zip(vectors_objects, expected_gloves):
                for word in expected_glove.keys():
                    self.assertEqual(vectors_obj[word][:3], expected_glove[word])

    def test_vocab_from_file(self):
        asset_name = 'vocab_test.txt'
        asset_path = get_asset_path(asset_name)
        with open(asset_path, 'r') as f:
            v = vocab_from_file(f, unk_token='<new_unk>')
            expected_itos = ['<new_unk>', 'b', 'a', 'c']
            expected_stoi = {x: index for index, x in enumerate(expected_itos)}
            self.assertEqual(v.get_itos(), expected_itos)
            self.assertEqual(dict(v.get_stoi()), expected_stoi)

    def test_vocab_from_raw_text_file(self):
        asset_name = 'vocab_raw_text_test.txt'
        asset_path = get_asset_path(asset_name)
        with open(asset_path, 'r') as f:
            tokenizer = basic_english_normalize()
            jit_tokenizer = torch.jit.script(tokenizer.to_ivalue())
            v = vocab_from_raw_text_file(f, jit_tokenizer, unk_token='<new_unk>')
            expected_itos = ['<new_unk>', "'", 'after', 'talks', '.', 'are', 'at', 'disappointed',
                             'fears', 'federal', 'firm', 'for', 'mogul', 'n', 'newall', 'parent',
                             'pension', 'representing', 'say', 'stricken', 't', 'they', 'turner',
                             'unions', 'with', 'workers']
            expected_stoi = {x: index for index, x in enumerate(expected_itos)}
            self.assertEqual(v.get_itos(), expected_itos)
            self.assertEqual(dict(v.get_stoi()), expected_stoi)