export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-16">
      <div className="flex w-full max-w-md flex-col items-center gap-6 text-center">
        <div className="size-32 rounded-full bg-gradient-to-br from-pink-300 to-purple-400 shadow-lg" />
        <h1 className="text-4xl font-bold tracking-tight">모모링</h1>
        <p className="text-lg text-zinc-600 dark:text-zinc-400">
          친구처럼 이야기하고, 함께 알아가요.
        </p>
        <button
          type="button"
          disabled
          className="mt-4 inline-flex h-12 items-center justify-center rounded-full bg-zinc-900 px-8 text-base font-medium text-white opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          시작하기 (준비 중)
        </button>
        <p className="text-xs text-zinc-500">
          음성 캡처와 대화 기능은 다음 PR에서 연결됩니다.
        </p>
      </div>
    </main>
  );
}
