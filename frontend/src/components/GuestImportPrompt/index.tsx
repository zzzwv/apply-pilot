import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Button, Modal, Typography } from "antd";
import type { QueryClient } from "@tanstack/react-query";

import { listApplications } from "../../api/applications";
import { LocalApplicationRepository } from "../../local-db/applicationRepository";
import { importGuestApplications, type GuestImportOutcome } from "../../sync/guestImport";
import { useAuthStore } from "../../store/auth";

const guestRepository = new LocalApplicationRepository("guest");
const dismissedUserIds = new Set<string>();

type Props = { queryClient: QueryClient };

async function refreshCloudData(queryClient: QueryClient, userId: string): Promise<void> {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["applications", "cloud", userId] }),
    queryClient.invalidateQueries({ queryKey: ["dashboard", "cloud", userId] }),
    queryClient.invalidateQueries({ queryKey: ["application"] }),
  ]);
  await listApplications({ page: 1, page_size: 20 });
  await Promise.all([
    queryClient.refetchQueries({ queryKey: ["applications", "cloud", userId], type: "active" }),
    queryClient.refetchQueries({ queryKey: ["dashboard", "cloud", userId], type: "active" }),
  ]);
}

function resultMessage(outcome: GuestImportOutcome): string {
  if (outcome.migrated === 0) return "本地记录暂未同步，你可以稍后重试。";
  if (outcome.failed > 0) return `已同步 ${outcome.migrated} 条投递记录，${outcome.failed} 条未成功同步，可稍后重试。`;
  if (outcome.cloud_snapshot_failed) return "云端记录已同步，本地记录将于下次确认云端数据后清理。";
  return `已同步 ${outcome.migrated} 条投递记录。`;
}

export function GuestImportPrompt({ queryClient }: Props) {
  const { user, initialized } = useAuthStore();
  const [dismissed, setDismissed] = useState(false);
  const [notice, setNotice] = useState<string>();
  const syncing = useRef(false);
  const canDetect = initialized && Boolean(user);
  const count = useQuery({
    queryKey: ["guest-import", "count", user?.id],
    enabled: canDetect,
    queryFn: () => guestRepository.count(),
  });

  useEffect(() => {
    setDismissed(Boolean(user && dismissedUserIds.has(user.id)));
    setNotice(undefined);
  }, [user?.id]);

  const sync = useMutation({
    mutationFn: async () => {
      if (!user) throw new Error("No authenticated user");
      return importGuestApplications({
        userId: user.id,
        repository: guestRepository,
        refreshCloud: () => refreshCloudData(queryClient, user.id),
      });
    },
    onSuccess: async (outcome) => {
      setNotice(resultMessage(outcome));
      dismissedUserIds.add(user!.id);
      setDismissed(true);
      await queryClient.invalidateQueries({ queryKey: ["guest-import", "count", user!.id] });
    },
    onError: () => {
      setNotice("本地记录暂未同步，你可以稍后重试。");
    },
    onSettled: () => { syncing.current = false; },
  });

  if (!canDetect || count.data === undefined || count.data === 0 || dismissed) return notice ? <Typography.Text role="status">{notice}</Typography.Text> : null;

  return <Modal className="guest-import-modal" title="同步本地投递记录" open footer={null} closable={false}>
    <div className="guest-import-modal__content">
      <Typography.Text className="guest-import-modal__eyebrow">本地记录提示</Typography.Text>
      <Typography.Paragraph className="guest-import-modal__count">检测到 {count.data} 条本地投递记录</Typography.Paragraph>
      <Typography.Paragraph className="guest-import-modal__description">是否同步到当前账号？</Typography.Paragraph>
      <div className="guest-import-modal__actions">
        <Button
          type="primary"
          loading={sync.isPending}
          disabled={sync.isPending}
          onClick={() => {
            if (syncing.current) return;
            syncing.current = true;
            sync.mutate();
          }}
        >
          同步到账号
        </Button>
        <Button disabled={sync.isPending} onClick={() => {
          dismissedUserIds.add(user!.id);
          setDismissed(true);
        }}>
          暂不同步
        </Button>
      </div>
    </div>
  </Modal>;
}
