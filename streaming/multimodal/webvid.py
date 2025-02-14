# Copyright 2023 MosaicML Streaming authors
# SPDX-License-Identifier: Apache-2.0

"""A streaming WebVid dataset."""

import os
from time import sleep
from typing import Any, Optional

from streaming.base import StreamingDataset
from streaming.base.dataset import TICK, _PartitionState
from streaming.base.storage import download


class StreamingInsideWebVid(StreamingDataset):
    """Streaming WebVid dataset.

    Videos are stored "inside" the shards, as is typically done.

    Args:
        local (str): Local dataset directory where shards are cached by split.
        remote (str, optional): Download shards from this remote path or directory. If None, this
            rank and worker's partition of the dataset must all exist locally. Defaults to
            ``None``.
        split (str, optional): Which dataset split to use, if any. Defaults to ``None``.
        shuffle (bool): Whether to iterate over the samples in randomized order. Defaults to
            ``False``.
        predownload (int, optional): Target number of samples ahead to download the shards of while
            iterating. Defaults to ``100_000``.
        keep_zip (bool, optional): Whether to keep or delete the compressed file when
            decompressing downloaded shards. If set to None, keep iff remote is local. Defaults to
            ``None``.
        download_retry (int): Number of download re-attempts before giving up. Defaults to ``2``.
        download_timeout (float): Number of seconds to wait for a shard to download before raising
            an exception. Defaults to ``60``.
        validate_hash (str, optional): Optional hash or checksum algorithm to use to validate
            shards. Defaults to ``None``.
        shuffle_seed (int): Seed for Deterministic data shuffling. Defaults to ``9176``.
        num_canonical_nodes (int, optional): Canonical number of nodes for shuffling with
            resumption. Defaults to ``None``, which is interpreted as the number of nodes of the
            initial run.
        batch_size (int, optional): Batch size of its DataLoader, which affects how the dataset is
            partitioned over the workers. Defaults to ``None``.
    """

    def __getitem__(self, idx: int) -> Any:
        """Get the sample at the index.

        Args:
            idx (int): Sample index.

        Returns:
            Any: The sample.
        """
        obj = super().__getitem__(idx)
        # Processing goes here.
        return obj


class StreamingOutsideGIWebVid(StreamingDataset):
    """Streaming WebVid dataset.

    Videos are stored "outside" the shards, as a file per video. The extra download happens in
    __getitem__ ("GI"), when samples are requested by the dataloader.

    Args:
        local (str): Local dataset directory where shards are cached by split.
        remote (str, optional): Download shards from this remote path or directory. If None, this
            rank and worker's partition of the dataset must all exist locally. Defaults to
            ``None``.
        split (str, optional): Which dataset split to use, if any. Defaults to ``None``.
        shuffle (bool): Whether to iterate over the samples in randomized order. Defaults to
            ``False``.
        predownload (int, optional): Target number of samples ahead to download the shards of while
            iterating. Defaults to ``100_000``.
        keep_zip (bool, optional): Whether to keep or delete the compressed file when
            decompressing downloaded shards. If set to None, keep iff remote is local. Defaults to
            ``None``.
        download_retry (int): Number of download re-attempts before giving up. Defaults to ``2``.
        download_timeout (float): Number of seconds to wait for a shard to download before raising
            an exception. Defaults to ``60``.
        validate_hash (str, optional): Optional hash or checksum algorithm to use to validate
            shards. Defaults to ``None``.
        shuffle_seed (int): Seed for Deterministic data shuffling. Defaults to ``9176``.
        num_canonical_nodes (int, optional): Canonical number of nodes for shuffling with
            resumption. Defaults to ``None``, which is interpreted as the number of nodes of the
            initial run.
        batch_size (int, optional): Batch size of its DataLoader, which affects how the dataset is
            partitioned over the workers. Defaults to ``None``.
        extra_local (str, optional): Base destination of extra local sample downloads.
        extra_remote (str, optional): Base source of extra remote sample downloads.
    """

    def __init__(self,
                 local: str,
                 remote: Optional[str] = None,
                 split: Optional[str] = None,
                 shuffle: bool = False,
                 predownload: Optional[int] = 100_000,
                 keep_zip: Optional[bool] = None,
                 download_retry: int = 2,
                 download_timeout: float = 60,
                 validate_hash: Optional[str] = None,
                 shuffle_seed: int = 9176,
                 num_canonical_nodes: Optional[int] = None,
                 batch_size: Optional[int] = None,
                 extra_local: Optional[str] = None,
                 extra_remote: Optional[str] = None):
        super().__init__(local, remote, split, shuffle, predownload, keep_zip, download_retry,
                         download_timeout, validate_hash, shuffle_seed, num_canonical_nodes,
                         batch_size)

        # Videos are stored outside of their shards here.
        self.extra_local = extra_local
        self.extra_remote = extra_remote

    def __getitem__(self, idx: int) -> Any:
        """Get the sample at the index.

        Args:
            idx (int): Sample index.

        Returns:
            Any: The sample.
        """
        obj = super().__getitem__(idx)

        if self.extra_local and self.extra_remote:
            rel_path = obj['content_path']
            local = os.path.join(self.extra_local, rel_path)
            remote = os.path.join(self.extra_remote, rel_path)
            if not os.path.exists(local):
                download(remote, local, self.download_timeout)
            with open(local, 'rb') as fp:
                content = fp.read()
            obj['content'] = content

        # Processing goes here.

        return obj


class StreamingOutsideDTWebVid(StreamingDataset):
    """Streaming WebVid dataset.

    Videos are stored "outside" the shards, as a file per video. The extra download happens in
    _download_thread ("DT"), when the download thread prefetches the sample.

    Args:
        local (str): Local dataset directory where shards are cached by split.
        remote (str, optional): Download shards from this remote path or directory. If None, this
            rank and worker's partition of the dataset must all exist locally. Defaults to
            ``None``.
        split (str, optional): Which dataset split to use, if any. Defaults to ``None``.
        shuffle (bool): Whether to iterate over the samples in randomized order. Defaults to
            ``False``.
        predownload (int, optional): Target number of samples ahead to download the shards of while
            iterating. Defaults to ``100_000``.
        keep_zip (bool, optional): Whether to keep or delete the compressed file when
            decompressing downloaded shards. If set to None, keep iff remote is local. Defaults to
            ``None``.
        download_retry (int): Number of download re-attempts before giving up. Defaults to ``2``.
        download_timeout (float): Number of seconds to wait for a shard to download before raising
            an exception. Defaults to ``60``.
        validate_hash (str, optional): Optional hash or checksum algorithm to use to validate
            shards. Defaults to ``None``.
        shuffle_seed (int): Seed for Deterministic data shuffling. Defaults to ``9176``.
        num_canonical_nodes (int, optional): Canonical number of nodes for shuffling with
            resumption. Defaults to ``None``, which is interpreted as the number of nodes of the
            initial run.
        batch_size (int, optional): Batch size of its DataLoader, which affects how the dataset is
            partitioned over the workers. Defaults to ``None``.
        extra_local (str, optional): Base destination of extra local sample downloads.
        extra_remote (str, optional): Base source of extra remote sample downloads.
    """

    def __init__(self,
                 local: str,
                 remote: Optional[str] = None,
                 split: Optional[str] = None,
                 shuffle: bool = False,
                 predownload: Optional[int] = 100_000,
                 keep_zip: Optional[bool] = None,
                 download_retry: int = 2,
                 download_timeout: float = 60,
                 validate_hash: Optional[str] = None,
                 shuffle_seed: int = 9176,
                 num_canonical_nodes: Optional[int] = None,
                 batch_size: Optional[int] = None,
                 extra_local: Optional[str] = None,
                 extra_remote: Optional[str] = None):
        super().__init__(local, remote, split, shuffle, predownload, keep_zip, download_retry,
                         download_timeout, validate_hash, shuffle_seed, num_canonical_nodes,
                         batch_size)

        # Videos are stored outside of their shards here.
        self.extra_local = extra_local
        self.extra_remote = extra_remote

    def __getitem__(self, idx: int) -> Any:
        """Get the sample at the index.

        Args:
            idx (int): Sample index.

        Returns:
            Any: The sample.
        """
        obj = super().__getitem__(idx)

        if self.extra_local and self.extra_remote:
            rel_path = obj['content_path']
            local = os.path.join(self.extra_local, rel_path)
            remote = os.path.join(self.extra_remote, rel_path)
            if not os.path.exists(local):
                download(remote, local, self.download_timeout)
            with open(local, 'rb') as fp:
                content = fp.read()
            obj['content'] = content

        # Processing goes here.

        return obj

    def _download_thread(self, state: _PartitionState) -> None:
        """Download the relevant shards in the background while we are being iterated.

        This thread is started at the beginning of each epoch, and exits either when out of samples
        or when a new epoch is started, calling stop() on its state (only one epoch is valid at a
        time).

        Each worker has its own download thread, which iterates ahead of the main thread.

        Args:
            state (_PartitionState): The partition state.
        """
        shard_states_lock, shard_states = self._get_shard_states()

        # Download loop.
        while True:
            # If we've started a new epoch early (__iter__ was called again), exit this thread
            # because there can only be one epoch at once.
            if state.is_stopped:
                break

            # If we're out of samples this epoch, exit this thread because we are done downloading.
            if state.download_index == state.total:
                break

            # If we are requested to only pre-download so many samples, if we have as many or more
            # downloaded already, we wait and check again later.
            if self.predownload is not None:
                samples_ahead = state.download_index - state.yield_index
                if self.predownload <= samples_ahead:
                    sleep(TICK)
                    continue

            # If we hit -1, we skip.
            sample_id = state.sample_ids[state.download_index]
            if sample_id == -1:
                state.download_index += 1
                continue

            # Download and decompress the shard for this sample, if not already done.
            shard_id, _ = self.index.find_sample(sample_id)
            self._download_or_skip_shard(shard_states_lock, shard_states, shard_id, False)

            # Predownload the sample's extra data.
            obj = super().__getitem__(sample_id)
            if self.extra_local and self.extra_remote:
                rel_path = obj['content_path']
                local = os.path.join(self.extra_local, rel_path)
                remote = os.path.join(self.extra_remote, rel_path)
                if not os.path.exists(local):
                    download(remote, local, self.download_timeout)

            state.download_index += 1
