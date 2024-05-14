import logging
from pathlib import Path

import lightning as L
import numpy as np
import torch as th
from lightning.pytorch import seed_everything
from torch.utils.data import DataLoader

from mamkit.configs.base import ConfigKey
from mamkit.configs.text import BiLSTMConfig
from mamkit.data.collators import UnimodalCollator, TextCollator
from mamkit.data.datasets import UKDebates, InputMode
from mamkit.data.processing import VocabBuilder, UnimodalProcessor
from mamkit.models.text import BiLSTM
from mamkit.utility.model import to_lighting_model
from lightning.pytorch.callbacks import EarlyStopping
from mamkit.utility.callbacks import PycharmProgressBar

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    save_path = Path(__file__).parent.resolve()

    loader = UKDebates(task_name='asd',
                       input_mode=InputMode.TEXT_ONLY)

    config = BiLSTMConfig.from_config(key=ConfigKey(dataset='ukdebates',
                                                    input_mode=InputMode.TEXT_ONLY,
                                                    task_name='asd',
                                                    tags='mancini-et-al-2022'))
    metrics = {}
    for seed in config.seeds:
        seed_everything(seed=seed)
        for split_info in loader.get_splits(key='mancini-et-al-2022'):
            processor = UnimodalProcessor(features_processor=VocabBuilder(tokenizer=config.tokenizer,
                                                                          embedding_model=config.embedding_model,
                                                                          embedding_dim=config.embedding_dim))
            processor.fit(train_data=split_info.train)

            split_info.train = processor(split_info.train)
            split_info.val = processor(split_info.val)
            split_info.test = processor(split_info.test)

            processor.clear()

            unimodal_collator = UnimodalCollator(
                features_collator=TextCollator(tokenizer=config.tokenizer,
                                               vocab=processor.features_processor.vocab),
                label_collator=lambda labels: th.tensor(labels)
            )

            train_dataloader = DataLoader(split_info.train,
                                          batch_size=config.batch_size,
                                          shuffle=True,
                                          collate_fn=unimodal_collator)
            val_dataloader = DataLoader(split_info.val,
                                        batch_size=config.batch_size,
                                        shuffle=False,
                                        collate_fn=unimodal_collator)
            test_dataloader = DataLoader(split_info.test,
                                         batch_size=config.batch_size,
                                         shuffle=False,
                                         collate_fn=unimodal_collator)

            model = BiLSTM(vocab_size=len(processor.features_processor.vocab),
                           embedding_dim=config.embedding_dim,
                           dropout_rate=config.dropout_rate,
                           lstm_weights=config.lstm_weights,
                           mlp_weights=config.mlp_weights,
                           num_classes=config.num_classes,
                           embedding_matrix=processor.features_processor.embedding_matrix
                           )
            model = to_lighting_model(model=model,
                                      loss_function=th.nn.CrossEntropyLoss(),
                                      num_classes=config.num_classes,
                                      optimizer_class=config.optimizer,
                                      **config.optimizer_args)

            trainer = L.Trainer(max_epochs=200,
                                accelerator='gpu',
                                callbacks=[EarlyStopping(monitor='val_loss', mode='min', patience=20),
                                           PycharmProgressBar()])
            trainer.fit(model,
                        train_dataloaders=train_dataloader,
                        val_dataloaders=val_dataloader)

            val_metrics = trainer.test(model, val_dataloader)[0]
            test_metrics = trainer.test(model, test_dataloader)[0]
            logging.info(f'Validation metrics: {val_metrics}')
            logging.info(f'Test metrics: {test_metrics}')

            for metric_name, metric_value in val_metrics.items():
                metrics.setdefault('validation', {}).setdefault(metric_name, []).append(metric_value)
            for metric_name, metric_value in test_metrics.items():
                metrics.setdefault('test', {}).setdefault(metric_name, []).append(metric_value)

            # reset
            processor.reset()

    # Averaging
    metric_names = list(metrics['validation'].keys())
    for split_name in ['validation', 'test']:
        for metric_name in metric_names:
            metric_values = np.array(metrics[split_name][metric_name]).reshape(len(config.seeds[:1]), -1)
            per_seed_avg = metric_values.mean(axis=-1)
            per_seed_std = metric_values.std(axis=-1)
            avg = per_seed_avg.mean(axis=-1)
            std = per_seed_avg.std(axis=-1)
            metrics[split_name][f'per_seed_avg_{metric_name}'] = (per_seed_avg, per_seed_std)
            metrics[split_name][f'avg_{metric_name}'] = (avg, std)

    logging.info(metrics)
    np.save(save_path.joinpath('metrics.npy').as_posix(), metrics)