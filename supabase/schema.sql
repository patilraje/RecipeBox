-- RecipeBox Supabase schema
-- Run this in the Supabase SQL Editor (Dashboard → SQL → New query)

-- Pantry settings per user
create table if not exists public.pantry_settings (
  user_id uuid primary key references auth.users (id) on delete cascade,
  basic text[] not null default '{}',
  optional_enabled text[] not null default '{}',
  updated_at timestamptz not null default now()
);

-- Saved favourite recipes
create table if not exists public.saved_recipes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  recipe_id text not null,
  recipe jsonb not null,
  created_at timestamptz not null default now(),
  unique (user_id, recipe_id)
);

create index if not exists saved_recipes_user_id_idx on public.saved_recipes (user_id);

alter table public.pantry_settings enable row level security;
alter table public.saved_recipes enable row level security;

-- Pantry policies
drop policy if exists "Users read own pantry" on public.pantry_settings;
create policy "Users read own pantry"
  on public.pantry_settings for select
  using (auth.uid() = user_id);

drop policy if exists "Users insert own pantry" on public.pantry_settings;
create policy "Users insert own pantry"
  on public.pantry_settings for insert
  with check (auth.uid() = user_id);

drop policy if exists "Users update own pantry" on public.pantry_settings;
create policy "Users update own pantry"
  on public.pantry_settings for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Saved recipes policies
drop policy if exists "Users read own recipes" on public.saved_recipes;
create policy "Users read own recipes"
  on public.saved_recipes for select
  using (auth.uid() = user_id);

drop policy if exists "Users insert own recipes" on public.saved_recipes;
create policy "Users insert own recipes"
  on public.saved_recipes for insert
  with check (auth.uid() = user_id);

drop policy if exists "Users delete own recipes" on public.saved_recipes;
create policy "Users delete own recipes"
  on public.saved_recipes for delete
  using (auth.uid() = user_id);

drop policy if exists "Users update own recipes" on public.saved_recipes;
create policy "Users update own recipes"
  on public.saved_recipes for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Categorized grocery lists
create table if not exists public.grocery_lists (
  user_id uuid primary key references auth.users (id) on delete cascade,
  categories jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.grocery_lists enable row level security;

drop policy if exists "Users read own grocery" on public.grocery_lists;
create policy "Users read own grocery"
  on public.grocery_lists for select
  using (auth.uid() = user_id);

drop policy if exists "Users insert own grocery" on public.grocery_lists;
create policy "Users insert own grocery"
  on public.grocery_lists for insert
  with check (auth.uid() = user_id);

drop policy if exists "Users update own grocery" on public.grocery_lists;
create policy "Users update own grocery"
  on public.grocery_lists for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "Users delete own grocery" on public.grocery_lists;
create policy "Users delete own grocery"
  on public.grocery_lists for delete
  using (auth.uid() = user_id);
