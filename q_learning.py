from collections import defaultdict
from logger import Logger
from numpy import random

import numpy as np


class QLearning:
    _unhashable_error_texts = "The state must be hashable, please use 'state_filter' in QLearning.__init__"

    def __init__(self, env, epsilon, gamma, alpha, log_frequency=100, state_filter=None, action_filter=None,
                 reward_filter=None, done_filter=None):
        """
        Initialization
        1. The 'env' should be gym-like.
        2. The state of 'env' should be hashable.
        3. The action of 'env' should be consistent with 'env.action_space.sample()'.
        4. The reward of 'env' should be numeric type.
        5. The done flag of 'env' should be bool type.

        :param env: A initialized gym (or gym-like) environment
        :param epsilon: Epsilon
        :param gamma: Discounted factor
        :param alpha: Learning rate
        :param log_frequency: The frequency of logging
        :param state_filter: The function which filters state of 'env' for QLearning algorithm
        :param action_filter: The function which filters chosen action of QLearning algorithm for 'env'
        :param reward_filter: The function which filters reward of 'env' for QLearning algorithm
        :param done_filter: The function which filters done flag of 'env' for QLearning algorithm
        """

        self.env = env
        self.epsilon = epsilon
        self.gamma = gamma
        self.alpha = alpha
        self.log_frequency = log_frequency
        self.state_wrapper = (lambda x: x) if state_filter is None else state_filter
        self.action_filter = (lambda x: x) if action_filter is None else action_filter
        self.reward_filter = (lambda x: x) if reward_filter is None else reward_filter
        self.done_filter = (lambda x: x) if done_filter is None else done_filter

        # Initialize Q function.
        self._q_func = defaultdict(lambda: random.random(self.env.action_space.n))

    def train(self, num_steps, render=False):
        rewards = []

        with Logger(num_steps, self.log_frequency, rewards) as logger:
            step_count = 0

            while step_count < num_steps:
                state = self.env.reset()
                state = self.state_wrapper(state)

                reward_sum = 0  # Sum of reward in an episode
                while True:
                    if render:
                        self.env.render()

                    step_count += 1

                    # Select action using epsilon greedy policy.
                    action = self._policy(state)
                    next_state, reward, done, _ = self.env.step(self.action_filter(action))
                    next_state = self.state_wrapper(next_state)
                    reward = self.reward_filter(reward)
                    done = self.done_filter(done)

                    reward_sum += reward

                    # Update Q Function using TD target.
                    next_action = np.argmax(self._get_action_values(next_state))
                    target = reward + self.gamma * self._get_q_value(next_state, next_action)
                    err = target - self._get_q_value(state, action)
                    self._update_q_value(state, action, err)

                    state = next_state

                    # Logging
                    if step_count % self.log_frequency == 0:
                        logger.update(self.log_frequency)

                    if done or step_count >= num_steps:
                        break
                rewards.append(reward_sum)

    def test(self, num_episodes, render=True):
        rewards = []

        for _ in range(num_episodes):
            state = self.env.reset()
            state = self.state_wrapper(state)
            done = False

            reward_sum = 0
            while not done:
                if render:
                    self.env.render()

                action = np.argmax(self._q_func[state])
                state, reward, done, _ = self.env.step(self.action_filter(action))
                reward = self.reward_filter(reward)
                done = self.done_filter(done)

                state = self.state_wrapper(state)
                reward_sum += reward

            rewards.append(reward_sum)

        print('Avg Reward: %.2f' % (sum(rewards) / len(rewards)))

    def _policy(self, state):
        if random.random() < self.epsilon:
            return self.env.action_space.sample()
        else:
            return np.argmax(self._q_func[state])

    def _get_q_value(self, state, action):
        return self._get_action_values(state)[action]

    def _update_q_value(self, state, action, err):
        self._get_action_values(state)[action] += self.alpha * err

    def _set_q_value(self, state, action, value):
        self._get_action_values(state)[action] = value

    def _get_action_values(self, state):
        try:
            return self._q_func[state]
        except TypeError:
            print(QLearning._unhashable_error_texts)
