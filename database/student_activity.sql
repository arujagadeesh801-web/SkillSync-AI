create table if not exists public.predictions (
    id bigint generated always as identity primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    study_hours double precision not null,
    attendance double precision not null,
    sleep_hours double precision not null,
    internet_usage double precision not null,
    assignments_completed double precision not null,
    previous_score double precision not null,
    predicted_score double precision not null,
    performance text not null,
    created_at timestamptz not null default now()
);

create index if not exists predictions_user_created_at_idx
    on public.predictions (user_id, created_at desc);

alter table public.predictions enable row level security;

grant select, insert on public.predictions to authenticated;
grant usage, select on sequence public.predictions_id_seq to authenticated;

drop policy if exists "Users can view their own predictions"
    on public.predictions;

create policy "Users can view their own predictions"
    on public.predictions
    for select
    to authenticated
    using ((select auth.uid()) = user_id);

drop policy if exists "Users can create their own predictions"
    on public.predictions;

create policy "Users can create their own predictions"
    on public.predictions
    for insert
    to authenticated
    with check ((select auth.uid()) = user_id);

create table if not exists public.quiz_results (
    id bigint generated always as identity primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    score integer not null check (score >= 0),
    total_questions integer not null check (total_questions > 0),
    created_at timestamptz not null default now()
);

create index if not exists quiz_results_user_created_at_idx
    on public.quiz_results (user_id, created_at desc);

alter table public.quiz_results enable row level security;

grant select, insert on public.quiz_results to authenticated;
grant usage, select on sequence public.quiz_results_id_seq to authenticated;

drop policy if exists "Users can view their own quiz results"
    on public.quiz_results;

create policy "Users can view their own quiz results"
    on public.quiz_results
    for select
    to authenticated
    using ((select auth.uid()) = user_id);

drop policy if exists "Users can create their own quiz results"
    on public.quiz_results;

create policy "Users can create their own quiz results"
    on public.quiz_results
    for insert
    to authenticated
    with check ((select auth.uid()) = user_id);
