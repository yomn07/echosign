import json
import time
import math

from pathlib import Path
from collections import defaultdict

import torch
import torch.nn as nn

from torch.utils.data import DataLoader


def sign_collate_fn(batch):

    features = [x[0] for x in batch]
    labels = [x[1] for x in batch]
    lengths = [x[2] for x in batch]


    max_len = max(lengths)


    padded = []

    for feat in features:

        pad = max_len - feat.shape[0]

        if pad > 0:

            zeros = torch.zeros(
                pad,
                feat.shape[1],
                dtype=feat.dtype
            )

            feat = torch.cat(
                [feat, zeros],
                dim=0
            )

        padded.append(feat)


    return (
        torch.stack(padded),
        torch.tensor(labels, dtype=torch.long),
        torch.tensor(lengths, dtype=torch.long)
    )


class WarmupCosineScheduler:

    def __init__(
        self,
        optimizer,
        warmup_epochs,
        total_epochs,
        base_lr
    ):

        self.optimizer = optimizer
        self.warmup_epochs = warmup_epochs
        self.total_epochs = total_epochs
        self.base_lr = base_lr
        self.last_epoch = -1



    def step(self):

        self.last_epoch += 1

        epoch = self.last_epoch


        if epoch < self.warmup_epochs:

            lr = self.base_lr * (
                (epoch + 1)
                /
                self.warmup_epochs
            )

        else:

            progress = (
                epoch - self.warmup_epochs
            ) / (
                self.total_epochs - self.warmup_epochs
            )


            lr = self.base_lr * 0.5 * (
                1 +
                math.cos(math.pi * progress)
            )


        for group in self.optimizer.param_groups:
            group["lr"] = lr



    def state_dict(self):

        return {
            "last_epoch": self.last_epoch
        }



    def load_state_dict(self, state):

        self.last_epoch = state["last_epoch"]


class Trainer:


    def __init__(
        self,
        model,
        train_dataset,
        val_dataset,
        checkpoint_dir,
        batch_size=32,
        learning_rate=1e-4,
        epochs=120,
        device=None,
        class_weights=None,
    ):


        self.model = model


        self.device = device or (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )


        self.model.to(self.device)



        self.checkpoint_dir = Path(
            checkpoint_dir
        )

        self.checkpoint_dir.mkdir(
            exist_ok=True,
            parents=True
        )



        self.train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            collate_fn=sign_collate_fn,
            num_workers=0,
            pin_memory=True
        )


        self.val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            collate_fn=sign_collate_fn,
            num_workers=0,
            pin_memory=True
        )



        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=1e-4
        )



        self.scheduler = WarmupCosineScheduler(
            self.optimizer,
            warmup_epochs=10,
            total_epochs=epochs,
            base_lr=learning_rate
        )

        self.loss_fn = nn.CrossEntropyLoss(
            weight=class_weights,
            label_smoothing=0.1
        )



        # AMP
        self.scaler = torch.cuda.amp.GradScaler(
            enabled=self.device=="cuda"
        )



        self.history = {
            "train_loss": [],
            "val_loss": [],
            "val_acc": [],
            "val_top5": []
        }


        self.best_acc = 0



    def train_one_epoch(self):

        self.model.train()

        total_loss = 0


        for features, labels, lengths in self.train_loader:


            features = features.to(
                self.device,
                non_blocking=True
            )

            labels = labels.to(
                self.device,
                non_blocking=True
            )

            lengths = lengths.to(
                self.device,
                non_blocking=True
            )


            self.optimizer.zero_grad()



            with torch.cuda.amp.autocast(
                enabled=self.device=="cuda"
            ):


                logits = self.model(
                    features,
                    lengths
                )


                loss = self.loss_fn(
                    logits,
                    labels
                )


            self.scaler.scale(loss).backward()



            self.scaler.unscale_(
                self.optimizer
            )


            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(),
                5.0
            )



            self.scaler.step(
                self.optimizer
            )


            self.scaler.update()



            total_loss += loss.item()



        return total_loss / len(self.train_loader)



    @torch.no_grad()
    def validate(
        self,
        return_per_class=False
    ):


        self.model.eval()


        total_loss = 0
        correct = 0
        top5_correct = 0
        total = 0


        per_class_correct = defaultdict(int)
        per_class_total = defaultdict(int)



        for features, labels, lengths in self.val_loader:


            features = features.to(self.device)
            labels = labels.to(self.device)
            lengths = lengths.to(self.device)



            logits = self.model(
                features,
                lengths
            )


            loss = self.loss_fn(
                logits,
                labels
            )


            total_loss += loss.item()



            preds = logits.argmax(1)



            correct += (
                preds == labels
            ).sum().item()



            top5 = logits.topk(
                5,
                dim=1
            ).indices



            top5_correct += (
                top5 == labels.unsqueeze(1)
            ).any(1).sum().item()



            total += labels.size(0)



            if return_per_class:

                for p,l in zip(
                    preds.cpu(),
                    labels.cpu()
                ):

                    per_class_total[l.item()] += 1

                    if p.item()==l.item():
                        per_class_correct[l.item()] += 1



        loss = total_loss / len(self.val_loader)

        acc = correct / total

        top5 = top5_correct / total



        if return_per_class:

            pc = {
                k:
                per_class_correct[k]
                /
                per_class_total[k]

                for k in per_class_total
            }

            return loss, acc, top5, pc



        return loss, acc, top5



    def save_checkpoint(
        self,
        name,
        epoch
    ):

        torch.save(
            {
                "epoch":epoch,

                "model":
                self.model.state_dict(),

                "optimizer":
                self.optimizer.state_dict(),

                "scheduler":
                self.scheduler.state_dict(),

                "scaler":
                self.scaler.state_dict(),

                "history":
                self.history
            },

            self.checkpoint_dir / name
        )


    def load_checkpoint(self, path):
        checkpoint = torch.load(path, map_location=self.device)

        self.model.load_state_dict(checkpoint["model"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.scheduler.load_state_dict(checkpoint["scheduler"])
        self.scaler.load_state_dict(checkpoint["scaler"])

        self.history = checkpoint["history"]

        # Restore best accuracy
        if len(self.history["val_acc"]) > 0:
            self.best_acc = max(self.history["val_acc"])

        print(f"Resumed from epoch {checkpoint['epoch'] + 1}")

        return checkpoint["epoch"] + 1
    
    def fit(self, epochs=120, start_epoch=0):


        for epoch in range(start_epoch, epochs):


            start=time.time()





            train_loss = self.train_one_epoch()

            self.scheduler.step()


            val_loss,val_acc,val_top5 = self.validate()



            self.history["train_loss"].append(
                train_loss
            )

            self.history["val_loss"].append(
                val_loss
            )

            self.history["val_acc"].append(
                val_acc
            )

            self.history["val_top5"].append(
                val_top5
            )



            print(
                f"""
Epoch {epoch+1}/{epochs}
Train loss: {train_loss:.4f}
Val loss:   {val_loss:.4f}
Top1:       {val_acc:.4f}
Top5:       {val_top5:.4f}
Time:       {time.time()-start:.1f}s
"""
            )



            self.save_checkpoint(
                "last.pt",
                epoch
            )



            if val_acc > self.best_acc:

                self.best_acc = val_acc

                self.save_checkpoint(
                    "best.pt",
                    epoch
                )

                print(
                    "New best model saved"
                )



        with open(
            self.checkpoint_dir/"history.json",
            "w"
        ) as f:

            json.dump(
                self.history,
                f,
                indent=2
            )


        print(
            "Best validation accuracy:",
            self.best_acc
        )


        return self.history