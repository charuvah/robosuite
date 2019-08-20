import sys

#sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')

import os
import numpy as np

import robosuite
from robosuite.wrappers import TeleopWrapper, GymWrapper, IKWrapper

from stable_baselines.common.policies import MlpPolicy, MlpLstmPolicy, CnnLstmPolicy
from stable_baselines.common.vec_env import DummyVecEnv, SubprocVecEnv, VecEnv, VecFrameStack
from stable_baselines.results_plotter import load_results, ts2xy
from stable_baselines import PPO2
from stable_baselines.bench import Monitor

best_mean_reward, n_steps = -np.inf, 0

#name = '3stack_cnnlstm'
#name = 'lstm'
#name = '4stack_lstm_gripperobs'
name = 'teleop_lstm_objstate_test'
log_dir = "./checkpoints/reach/" + name + '/'
os.makedirs(log_dir, exist_ok=True)

def callback(_locals, _globals):
    global n_steps, best_mean_reward
    if (n_steps + 1) % 75 == 0:
        x, y = ts2xy(load_results(log_dir), 'timesteps')
        if len(x) > 0:
            mean_reward = np.mean(y[-100:])
            print(x[-1], 'timesteps')
            print("Best mean reward: {:.2f} - Last mean reward per episode: {:.2f}".format(best_mean_reward, mean_reward))

            if mean_reward > best_mean_reward:
                best_mean_reward = mean_reward
                print("Saving new best model")
                _locals['self'].save(log_dir + 'best_model.pkl')
    n_steps += 1
    return True

def main():
    num_stack = 1
    num_env = 1
    render = False
    image_state = False
    subproc = True
    existing = '/home/robot/andrewk/robosuite/robosuite/learning/checkpoints/reach/teleop_lstm_objstate_test/best_model.pkl'
    markov_obs = True
    finger_obs = False
    env_type = "SawyerReach"  # "SawyerLift"
    #arch = CnnLstmPolicy # MlpLstmPolicy  # MlpPolicy
    arch = MlpLstmPolicy  # MlpPolicy
    print('Config for ' + log_dir + ':')
    print('num_stack:', num_stack)
    print('num_env:', num_env)
    print('render:', render)
    print('image_state:', image_state)
    print('subproc:', subproc)
    print('existing:', existing)
    print('markov_obs:', markov_obs)
    print('log_dir:', log_dir)

    env = []
    for i in range(num_env):
        #ith = GymWrapper(IKWrapper(robosuite.make(env_type, has_renderer=render, has_offscreen_renderer=image_state, use_camera_obs=image_state, reward_shaping=True, camera_name='agentview'), markov_obs=markov_obs), num_stack=num_stack, keys=['object-state'])
        ith = GymWrapper(TeleopWrapper(robosuite.make(env_type, has_renderer=render, has_offscreen_renderer=image_state, use_camera_obs=image_state, reward_shaping=True, camera_name='agentview')), num_stack=num_stack, keys=['object-state'])
        ith.metadata = {'render.modes': ['human']}
        ith.reward_range = None
        ith.spec = None
        ith = Monitor(ith, log_dir, allow_early_resets=True)
        env.append((lambda: ith))

    if num_stack:
        env = VecFrameStack(SubprocVecEnv(env, 'fork'), num_stack) if subproc else VecFrameStack(DummyVecEnv(env), num_stack)
    else:
        env = SubprocVecEnv(env, 'fork') if subproc else DummyVecEnv(env)

    if existing:
        print('Loading pkl directly')
        model = PPO2.load(existing)
    else:
        try:
            print('Trying existing model...')
            model = PPO2.load(log_dir + 'best_model.pkl')
            model.set_env(env)
        except:
            print('No existing model found. Training new one.')
            model = PPO2(arch, env, verbose=1, nminibatches=num_env)

    if not existing:
        model.learn(total_timesteps=int(1e8), callback=callback)

    #if render:
    obs = env.reset()
    while True:
        obs = np.tile(obs, (8, 1))
        action, _states = model.predict(obs)
        obs, rewards, done, info = env.step(action)
        #env._get_target_envs([0])[0].render()
        if done[0]:
            obs = env.reset()

if __name__ == '__main__':
    main()

